#!/usr/bin/env python3
# main.py  –  Forex Crypto Signal Bot v11
#
# ENV VARS REQUIRED:
#   TELEGRAM_BOT_TOKEN
#   TELEGRAM_CHAT_ID
#   TWELVE_DATA_KEY      — free at twelvedata.com
#   PO_SSID              — from Pocket Option browser cookies (for OTC)

import asyncio
import os
import random
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
)

import config
import signal_generator as sg
import tracker
import websocket_client as wsc

# ─── ENV ─────────────────────────────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TWELVE_DATA_KEY  = os.getenv("TWELVE_DATA_KEY", "").strip().strip('"').strip("'")
PO_SSID          = os.getenv("PO_SSID", "").strip()

# ─── RUNTIME STATE ───────────────────────────────────────────────────────────
auto_signals_on: bool  = True
signal_count:    int   = 0
min_confidence:  int   = config.CONFIDENCE_DEFAULT
last_signal_time: dict = {}
user_balance:    float = 100.0   # default balance for stake suggestions
coingecko_ok:    bool  = False
er_api_ok:       bool  = False
td_ok:           bool  = False

# ─── TWELVE DATA RATE LIMITER ────────────────────────────────────────────────
_td_ts: list = []

def _td_wait():
    now = time.time()
    _td_ts[:] = [t for t in _td_ts if t > now - 60]
    if len(_td_ts) >= 7:
        time.sleep(61 - (now - _td_ts[0]))
    _td_ts.append(time.time())

# ─── FOREX: open.er-api.com ───────────────────────────────────────────────────
_er_cache: dict = {}
_er_cache_time: dict = {}

def fetch_er_all(base: str) -> dict:
    now = time.time()
    if base in _er_cache and now - _er_cache_time.get(base, 0) < 60:
        return _er_cache[base]
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=12)
        d = r.json()
        if d.get("result") == "success":
            _er_cache[base] = d["rates"]
            _er_cache_time[base] = now
            return d["rates"]
    except Exception as e:
        print(f"  [ER-API] {base}: {e}")
    return {}

def fetch_forex_price(symbol: str) -> float | None:
    info  = config.FOREX_PAIRS.get(symbol, {})
    # Parse base/quote from symbol string (e.g. EURUSD → EUR, USD)
    base  = symbol[:3]
    quote = symbol[3:]
    rates = fetch_er_all(base)
    rate  = rates.get(quote)
    if rate:
        print(f"  [ER-API] {symbol}: {rate}")
        return float(rate)
    return None

# ─── CRYPTO: CoinGecko ───────────────────────────────────────────────────────

def fetch_all_crypto_prices() -> dict:
    id_to_syms: dict = {}
    for sym, info in config.CRYPTO_PAIRS.items():
        id_to_syms.setdefault(info["cg_id"], []).append(sym)
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={','.join(id_to_syms)}&vs_currencies=usd",
            timeout=15,
        )
        data = r.json()
        result = {}
        for cg_id, syms in id_to_syms.items():
            if cg_id in data:
                price = float(data[cg_id]["usd"])
                for s in syms:
                    result[s] = price
        return result
    except Exception as e:
        print(f"  [CoinGecko] {e}")
        return {}

# ─── TWELVE DATA ─────────────────────────────────────────────────────────────

def fetch_td_price(symbol: str) -> float | None:
    if not TWELVE_DATA_KEY:
        return None
    _td_wait()
    try:
        r = requests.get(
            f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_KEY}",
            timeout=12,
        )
        d = r.json()
        if "price" in d:
            print(f"  [TD] {symbol}: {d['price']}")
            return float(d["price"])
        print(f"  [TD ERROR] {symbol}: {d.get('message', d)}")
    except Exception as e:
        print(f"  [TD] {symbol}: {e}")
    return None

# ─── API HEALTH ──────────────────────────────────────────────────────────────

def check_api_health():
    global coingecko_ok, er_api_ok, td_ok
    try:
        coingecko_ok = requests.get(
            "https://api.coingecko.com/api/v3/ping", timeout=8
        ).status_code == 200
    except Exception:
        coingecko_ok = False
    try:
        er_api_ok = requests.get(
            "https://open.er-api.com/v6/latest/USD", timeout=10
        ).json().get("result") == "success"
    except Exception:
        er_api_ok = False
    if TWELVE_DATA_KEY:
        try:
            td_ok = "price" in requests.get(
                f"https://api.twelvedata.com/price?symbol=AAPL&apikey={TWELVE_DATA_KEY}",
                timeout=10,
            ).json()
        except Exception:
            td_ok = False

# ─── SSID EXPIRY CALLBACK ────────────────────────────────────────────────────
# Called by websocket_client when SSID is rejected by Pocket Option.
_app_ref = None

async def _notify_ssid_expired():
    if _app_ref:
        await _app_ref.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=(
                "⚠️ *Pocket Option SSID has expired!*\n\n"
                "OTC prices are no longer available.\n\n"
                "To get a new SSID:\n"
                "1. Open pocketoption.com in Chrome on desktop\n"
                "2. Press F12 → Application tab\n"
                "3. Cookies → pocketoption.com\n"
                "4. Find `ssid` and copy its value\n"
                "5. Send: `/newssid YOUR_SSID_VALUE`\n\n"
                "_Regular forex and crypto signals continue normally._"
            ),
            parse_mode="Markdown",
        )

def _ssid_expired_sync():
    """Sync wrapper — schedules the async notification."""
    if _app_ref:
        asyncio.run_coroutine_threadsafe(
            _notify_ssid_expired(), _app_ref.updater.get_event_loop() if hasattr(_app_ref, 'updater') else asyncio.get_event_loop()
        )

# ─── SIGNAL DISPATCH ─────────────────────────────────────────────────────────

async def dispatch_signal(bot, category, symbol, pair_info, source, signal, manual=False) -> bool:
    if not manual and not auto_signals_on:
        return False
    if not manual and tracker.is_paused():
        print(f"  [PAUSED] {symbol}: consecutive loss pause active")
        return False

    global signal_count
    stake_info = sg.tracker.suggest_stake(signal["confidence"], user_balance) \
        if hasattr(sg, "tracker") else tracker.suggest_stake(signal["confidence"], user_balance)

    # Register with tracker to get signal ID
    now_wat    = datetime.now(tz=timezone(timedelta(hours=config.TIMEZONE_OFFSET)))
    entry_time = now_wat + timedelta(minutes=signal["entry_lead"])
    expiry     = entry_time + timedelta(minutes=signal["duration"])
    sid        = tracker.register_signal(signal, entry_time, expiry)

    msg = sg.format_signal_message(signal, pair_info, source, sid, stake_info)

    # Inline WIN/LOSS buttons
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ WIN  {sid}", callback_data=f"WIN:{sid}"),
        InlineKeyboardButton(f"❌ LOSS {sid}", callback_data=f"LOSS:{sid}"),
    ]])

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=msg,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    signal_count += 1
    last_signal_time[symbol] = time.time()
    print(f"  ✅ {sid} {symbol} {signal['direction']} score={signal['score']}/7 "
          f"conf={signal['confidence']}% dur={signal['duration']}min")
    return True

# ─── WIN/LOSS CALLBACK ───────────────────────────────────────────────────────

async def callback_result(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    data   = query.data  # "WIN:#042" or "LOSS:#042"
    parts  = data.split(":")
    if len(parts) != 2:
        return
    result, sid = parts[0], parts[1]
    entry  = tracker.record_result(sid, result)
    if entry is None:
        await query.edit_message_reply_markup(reply_markup=None)
        return

    emoji = "✅" if result == "WIN" else "❌"
    stats = tracker.get_statistics()
    await query.edit_message_text(
        query.message.text +
        f"\n\n{emoji} *Result recorded:* `{result}`\n"
        f"_Running win rate: {stats['win_rate']}% ({stats['wins']}W/{stats['losses']}L)_",
        parse_mode="Markdown",
    )

    # Notify if consecutive losses triggered a pause
    if tracker.is_paused():
        await ctx.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=(
                f"⏸ *Auto signals PAUSED*\n\n"
                f"_{config.MAX_CONSECUTIVE_LOSSES} consecutive losses detected._\n"
                f"_Paused for {config.LOSS_PAUSE_MINUTES} minutes to protect your account._\n\n"
                f"Use /resume to restart manually."
            ),
            parse_mode="Markdown",
        )

# ─── FULL SCAN ────────────────────────────────────────────────────────────────

async def run_full_scan(bot, force=False, manual=False) -> int:
    if not manual and not auto_signals_on:
        return 0
    if not manual and tracker.is_paused():
        print(f"[Scan] Paused — {tracker.pause_remaining_minutes()}min remaining")
        return 0

    print(f"\n{'='*50}\n[Scan] {'MANUAL' if manual else 'Auto'} scan\n{'='*50}")
    sent   = 0
    now_ts = time.time()

    # ── CRYPTO ───────────────────────────────────────────────────────────────
    prices = fetch_all_crypto_prices()
    items  = list(config.CRYPTO_PAIRS.items())
    random.shuffle(items)
    for sym, info in items:
        if sent >= config.MAX_SIGNALS_PER_SCAN:
            break
        if not force and now_ts - last_signal_time.get(sym, 0) < config.COOLDOWN_SECONDS:
            continue
        price = prices.get(sym)
        if price is None:
            continue
        sig = sg.evaluate_signal(sym, price, "crypto", min_confidence, force=force)
        if sig:
            ok = await dispatch_signal(bot, "crypto", sym, info, "CoinGecko", sig, manual)
            if ok:
                sent += 1
                await asyncio.sleep(1)

    # ── OTC (Pocket Option WebSocket) ────────────────────────────────────────
    if sent < config.MAX_SIGNALS_PER_SCAN and wsc.is_connected():
        otc_items = list(config.OTC_PAIRS.items())
        random.shuffle(otc_items)
        for sym, info in otc_items:
            if sent >= config.MAX_SIGNALS_PER_SCAN:
                break
            if not force and now_ts - last_signal_time.get(sym, 0) < config.COOLDOWN_SECONDS:
                continue
            price = wsc.get_otc_price(sym)
            if price is None:
                continue
            sg.record_price(sym, price)
            sig = sg.evaluate_signal(sym, price, "otc", min_confidence, force=force)
            if sig:
                ok = await dispatch_signal(bot, "otc", sym, info, "Pocket Option", sig, manual)
                if ok:
                    sent += 1
                    await asyncio.sleep(1)

    # ── FOREX ────────────────────────────────────────────────────────────────
    if sent < config.MAX_SIGNALS_PER_SCAN:
        fx_items = list(config.FOREX_PAIRS.items())
        random.shuffle(fx_items)
        for sym, info in fx_items:
            if sent >= config.MAX_SIGNALS_PER_SCAN:
                break
            if not force and now_ts - last_signal_time.get(sym, 0) < config.COOLDOWN_SECONDS:
                continue
            price = fetch_forex_price(sym)
            if price is None:
                continue
            sig = sg.evaluate_signal(sym, price, "forex", min_confidence, force=force)
            if sig:
                ok = await dispatch_signal(bot, "forex", sym, info, "ExchangeRate-API", sig, manual)
                if ok:
                    sent += 1
                    await asyncio.sleep(1)

    # ── INDICES / COMMODITIES / STOCKS ───────────────────────────────────────
    for cat in ("indices", "commodities", "stocks"):
        if sent >= config.MAX_SIGNALS_PER_SCAN or not TWELVE_DATA_KEY:
            break
        cat_items = list(config.get_all_pairs()[cat].items())
        random.shuffle(cat_items)
        for sym, info in cat_items:
            if sent >= config.MAX_SIGNALS_PER_SCAN:
                break
            if not force and now_ts - last_signal_time.get(sym, 0) < config.COOLDOWN_SECONDS:
                continue
            price = fetch_td_price(sym)
            if price is None:
                continue
            sig = sg.evaluate_signal(sym, price, cat, min_confidence, force=force)
            if sig:
                ok = await dispatch_signal(bot, cat, sym, info, "Twelve Data", sig, manual)
                if ok:
                    sent += 1
                    await asyncio.sleep(1)

    print(f"[Scan] Done — {sent} signal(s) sent")
    return sent

# ─── AUTO SCAN LOOP ──────────────────────────────────────────────────────────

async def auto_scan_loop(app):
    check_api_health()
    while True:
        interval = random.randint(
            config.SCAN_INTERVAL_MIN * 60, config.SCAN_INTERVAL_MAX * 60
        )
        print(f"[AutoScan] Next in {interval//60}m {interval%60}s")
        await asyncio.sleep(interval)
        if auto_signals_on:
            await run_full_scan(app.bot)

        # Signal expiry check
        expired = tracker.check_expired_signals()
        for sig in expired:
            try:
                await app.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=(
                        f"⚠️ *Signal Expired — DO NOT ENTER*\n\n"
                        f"`{sig['id']}` {sig['symbol']} {sig['direction']}\n"
                        f"_Entry window has passed. Skip this trade._"
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                pass

# ─── COMMANDS ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total = sum(len(v) for v in config.get_all_pairs().values())
    await update.message.reply_text(
        f"👋 *Forex Crypto Signal Bot v11*\n\n"
        f"🔬 *7-Indicator Engine*\n"
        f"_RSI · Stoch · MACD · BB · EMA · Divergence · ADX_\n"
        f"_Fires when {config.MIN_SCORE}/7 confirm_\n\n"
        f"📊 *{total} pairs* incl. real OTC from Pocket Option\n\n"
        f"📋 *Commands:*\n"
        f"`/build`          – Prime history now\n"
        f"`/scan`           – Force scan\n"
        f"`/history`        – History progress\n"
        f"`/status`         – API health\n"
        f"`/signal EURUSD`  – Check one pair\n"
        f"`/pairs`          – All pairs\n"
        f"`/autosignal`     – Toggle auto signals\n"
        f"`/resume`         – Resume after loss pause\n"
        f"`/balance 500`    – Set account balance\n"
        f"`/stats`          – Win/loss statistics\n"
        f"`/summary`        – Daily performance\n"
        f"`/newssid VALUE`  – Update PO SSID\n"
        f"`/debug`          – API connectivity test\n"
        f"`/confidence 60`  – Min confidence\n"
        f"`/time`           – Nigeria time\n",
        parse_mode="Markdown",
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    check_api_health()
    msg = sg.format_status_message(
        auto_signals_on, signal_count,
        coingecko_ok, er_api_ok, td_ok,
        wsc.is_connected(), min_confidence,
        tracker.is_paused(), tracker.pause_remaining_minutes(),
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_newssid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Update Pocket Option SSID when it expires."""
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: `/newssid YOUR_SSID_VALUE`", parse_mode="Markdown"
        )
        return
    new_ssid = args[0].strip()
    wsc.reset_ssid(new_ssid)
    await update.message.reply_text(
        "✅ *SSID updated!*\n_Reconnecting to Pocket Option …_\n"
        "_OTC prices will resume in a few seconds._",
        parse_mode="Markdown",
    )

async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global user_balance
    args = ctx.args
    if not args:
        await update.message.reply_text(
            f"⚠️ Usage: `/balance 500`\nCurrent: `${user_balance}`",
            parse_mode="Markdown",
        )
        return
    try:
        user_balance = float(args[0])
        await update.message.reply_text(
            f"✅ Balance set to `${user_balance:,.2f}`\n"
            f"_Stake suggestions will use this value._",
            parse_mode="Markdown",
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")

async def cmd_resume(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tracker.resume_manually()
    await update.message.reply_text(
        "✅ *Auto signals resumed.*\n_Consecutive loss counter reset._",
        parse_mode="Markdown",
    )

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = tracker.get_statistics()
    best  = tracker.get_best_pairs(3)
    worst = tracker.get_worst_pairs(3)
    bar   = "█" * int(stats["win_rate"] / 10) + "░" * (10 - int(stats["win_rate"] / 10))
    best_str  = ", ".join(f"`{p[0]}` {p[1]}%" for p in best[:3])  or "_N/A_"
    worst_str = ", ".join(f"`{p[0]}` {p[1]}%" for p in worst[:3]) or "_N/A_"
    await update.message.reply_text(
        f"📊 *Trading Statistics*\n"
        f"{'─'*32}\n"
        f"📨 Total signals:  `{stats['total']}`\n"
        f"✅ Wins:           `{stats['wins']}`\n"
        f"❌ Losses:         `{stats['losses']}`\n"
        f"🎯 Win Rate:       `{stats['win_rate']}%`\n"
        f"`[{bar}]`\n"
        f"💰 Profit Factor:  `{stats['profit_factor']}`\n"
        f"🏆 Best pairs:     {best_str}\n"
        f"⚠️ Worst pairs:   {worst_str}\n"
        f"🔴 Consec. losses: `{stats['consecutive_losses']}`\n",
        parse_mode="Markdown",
    )

async def cmd_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(tracker.daily_summary(), parse_mode="Markdown")

async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    needed     = config.MIN_PRICE_HISTORY
    total      = sum(len(v) for v in config.get_all_pairs().values())
    hist_ready = sum(1 for _, s in config.all_symbols_flat()
                     if sg.history_length(s) >= needed)
    await update.message.reply_text(
        f"🔄 *Scanning …*\n"
        f"_Ready: {hist_ready}/{total} pairs_\n"
        f"_Signals fire when {config.MIN_SCORE}/7 indicators align._",
        parse_mode="Markdown",
    )
    count = await run_full_scan(ctx.application.bot, force=True, manual=True)
    if count == 0:
        await update.message.reply_text(
            f"✅ Scan complete — no signals.\n"
            f"_{hist_ready}/{total} pairs evaluated._\n"
            f"_RSI neutral or < {config.MIN_SCORE}/7 indicators aligned._\n"
            f"_This is correct — conditions aren't right to trade._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"✅ `{count}` signal(s) sent!", parse_mode="Markdown"
        )

async def cmd_autosignal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global auto_signals_on
    auto_signals_on = not auto_signals_on
    if auto_signals_on:
        msg = (f"✅ *Auto signals ON*\n"
               f"_Scanning every {config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX} min._")
    else:
        msg = "❌ *Auto signals OFF*\n_Use /scan to trigger manually._"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    icons  = {"crypto":"🪙","forex":"💱","otc":"🔌","indices":"📈",
              "commodities":"⚗️","stocks":"🏢"}
    needed = config.MIN_PRICE_HISTORY
    lines  = [f"📈 *History Progress* _(need {needed} pts/pair)_\n"]
    tr = tp = 0
    for cat, pairs in config.get_all_pairs().items():
        ready = sum(1 for s in pairs if sg.history_length(s) >= needed)
        tr += ready; tp += len(pairs)
        lines.append(f"{icons[cat]} *{cat.capitalize()}*: `{ready}/{len(pairs)}`")
    lines += [f"\n📊 *Total: {tr}/{tp}*",
              "\n_Run /build to fill history in minutes._"]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    needed = config.MIN_PRICE_HISTORY
    total  = sum(len(v) for v in config.get_all_pairs().values())
    await update.message.reply_text(
        f"⚡ *Building price history …*\n_{needed} rounds of real prices._\n"
        "_You'll get a message when done._",
        parse_mode="Markdown",
    )
    bot = ctx.application.bot
    for rnd in range(1, needed + 1):
        prices = fetch_all_crypto_prices()
        for s, p in prices.items():
            sg.record_price(s, p)
        for sym in config.FOREX_PAIRS:
            p = fetch_forex_price(sym)
            if p:
                sg.record_price(sym, p)
        if TWELVE_DATA_KEY:
            for cat in ("indices", "commodities", "stocks"):
                for sym in config.get_all_pairs()[cat]:
                    p = fetch_td_price(sym)
                    if p:
                        sg.record_price(sym, p)
        # OTC prices from WebSocket (already streaming)
        for sym, p in wsc.all_otc_prices().items():
            sg.record_price(sym, p)

        ready = sum(1 for _, s in config.all_symbols_flat()
                    if sg.history_length(s) >= needed)
        print(f"[Build] Round {rnd}/{needed} — {ready}/{total} ready")
        if ready >= total:
            break
        if rnd % 5 == 0:
            try:
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⏳ Round {rnd}/{needed} — `{ready}/{total}` ready",
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        await asyncio.sleep(3)

    final = sum(1 for _, s in config.all_symbols_flat()
                if sg.history_length(s) >= needed)
    await update.message.reply_text(
        f"✅ *Build complete!* `{final}/{total}` pairs ready.\n_Run /scan now._",
        parse_mode="Markdown",
    )

async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global signal_count
    args = ctx.args
    if not args:
        await update.message.reply_text("⚠️ Usage: `/signal EURUSD`", parse_mode="Markdown")
        return
    symbol = args[0].upper()
    category, sym_key, pair_info = config.find_pair(symbol)
    if category is None:
        await update.message.reply_text(f"❌ Unknown: `{symbol}`", parse_mode="Markdown")
        return
    await update.message.reply_text(f"🔍 Fetching `{symbol}` …", parse_mode="Markdown")

    # Fetch price based on category
    if category == "crypto":
        prices = fetch_all_crypto_prices()
        price  = prices.get(sym_key)
        source = "CoinGecko"
    elif category == "otc":
        price  = wsc.get_otc_price(sym_key)
        source = "Pocket Option"
    elif category == "forex":
        price  = fetch_forex_price(sym_key)
        source = "ExchangeRate-API"
    else:
        price  = fetch_td_price(sym_key)
        source = "Twelve Data"

    if price is None:
        await update.message.reply_text(
            f"❌ No price for `{symbol}`. Use /debug.", parse_mode="Markdown"
        )
        return

    sg.record_price(sym_key, price)
    hist = sg.history_length(sym_key)
    if hist < config.MIN_PRICE_HISTORY:
        await update.message.reply_text(
            f"📊 `{symbol}` | `{price}` | History: `{hist}/{config.MIN_PRICE_HISTORY}`\n"
            f"_Run /build to fill history._", parse_mode="Markdown"
        )
        return

    sig = sg.evaluate_signal(sym_key, price, category, 0, force=True)
    if sig is None:
        rsi = sg.calculate_rsi(sg.get_price_history(sym_key))
        rsi_s = f"`{rsi:.2f}`" if rsi else "_N/A_"
        await update.message.reply_text(
            f"📊 `{symbol}` | Price: `{price}` | RSI: {rsi_s}\n"
            f"_Neutral zone or < {config.MIN_SCORE}/7 aligned. No signal._",
            parse_mode="Markdown",
        )
        return

    stake_info = tracker.suggest_stake(sig["confidence"], user_balance)
    now_wat    = datetime.now(tz=timezone(timedelta(hours=config.TIMEZONE_OFFSET)))
    entry_time = now_wat + timedelta(minutes=sig["entry_lead"])
    expiry     = entry_time + timedelta(minutes=sig["duration"])
    sid        = tracker.register_signal(sig, entry_time, expiry)
    msg        = sg.format_signal_message(sig, pair_info, source, sid, stake_info)
    keyboard   = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ WIN  {sid}", callback_data=f"WIN:{sid}"),
        InlineKeyboardButton(f"❌ LOSS {sid}", callback_data=f"LOSS:{sid}"),
    ]])
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
    last_signal_time[sym_key] = time.time()
    signal_count += 1

async def cmd_pairs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    icons = {"crypto":"🪙","forex":"💱","otc":"🔌","indices":"📈",
             "commodities":"⚗️","stocks":"🏢"}
    lines = ["📋 *All Monitored Pairs*\n"]
    total = 0
    for cat, pairs in config.get_all_pairs().items():
        lines.append(f"{icons[cat]} *{cat.capitalize()}* — {len(pairs)}")
        for s, i in pairs.items():
            lines.append(f"  `{s}` {i['flag']} {i['name']}")
        lines.append("")
        total += len(pairs)
    lines.append(f"📊 *Total: {total}*")
    text = "\n".join(lines)
    if len(text) > 4000:
        mid = len(lines) // 2
        await update.message.reply_text("\n".join(lines[:mid]), parse_mode="Markdown")
        await update.message.reply_text("\n".join(lines[mid:]), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_debug(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["🔬 *API Debug*\n"]
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        lines.append("✅ CoinGecko" if r.status_code == 200 else f"❌ CoinGecko HTTP {r.status_code}")
    except Exception as e:
        lines.append(f"❌ CoinGecko: `{e}`")
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        ngn = r.json().get("rates", {}).get("NGN", "N/A")
        lines.append(f"✅ ER-API _(USD/NGN≈{ngn})_"
                     if r.json().get("result") == "success" else "❌ ER-API")
    except Exception as e:
        lines.append(f"❌ ER-API: `{e}`")
    if TWELVE_DATA_KEY:
        try:
            r = requests.get(
                f"https://api.twelvedata.com/price?symbol=AAPL&apikey={TWELVE_DATA_KEY}",
                timeout=10,
            )
            d = r.json()
            lines.append(f"✅ Twelve Data _(AAPL=${d['price']})_"
                         if "price" in d else f"❌ Twelve Data: `{d.get('message')}`")
        except Exception as e:
            lines.append(f"❌ Twelve Data: `{e}`")
    else:
        lines.append("⚠️ Twelve Data: no key set")
    lines.append(f"\n🔌 PO WebSocket: {'✅ Connected' if wsc.is_connected() else '❌ Not connected'}")
    otc_count = len(wsc.all_otc_prices())
    lines.append(f"📡 OTC prices live: `{otc_count}/{len(config.OTC_PAIRS)}`")
    if wsc.is_ssid_expired():
        lines.append("⚠️ SSID expired — send `/newssid YOUR_VALUE`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat)
    await update.message.reply_text(
        f"🕐 *Nigeria Time (WAT / UTC+1)*\n"
        f"`{now.strftime('%A, %d %B %Y  %I:%M:%S %p')}`",
        parse_mode="Markdown",
    )

async def cmd_confidence(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global min_confidence
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            f"⚠️ `/confidence 60` | Current: `{min_confidence}%`",
            parse_mode="Markdown",
        )
        return
    val = int(args[0])
    if not 1 <= val <= 100:
        await update.message.reply_text("❌ Must be 1–100.")
        return
    min_confidence = val
    await update.message.reply_text(f"✅ Min confidence: `{min_confidence}%`", parse_mode="Markdown")

# ─── POST-INIT ───────────────────────────────────────────────────────────────

async def on_startup(app: Application):
    global _app_ref
    _app_ref = app

    # Start Pocket Option WebSocket if SSID is set
    if PO_SSID:
        wsc.start_websocket(PO_SSID, _ssid_expired_sync)
        print("[Main] PO WebSocket started.")
    else:
        print("[Main] PO_SSID not set — OTC disabled. Add it to Railway env vars.")

    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=sg.format_startup_message(ws_connected=bool(PO_SSID)),
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"[Startup] {e}")

    asyncio.create_task(auto_scan_loop(app))

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Forex Crypto Signal Bot v11")
    print("=" * 50)
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set.")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID not set.")
    if not TWELVE_DATA_KEY:
        print("[WARNING] TWELVE_DATA_KEY not set — stocks/indices/commodities disabled.")
    if not PO_SSID:
        print("[WARNING] PO_SSID not set — OTC pairs disabled.")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("signal",      cmd_signal))
    app.add_handler(CommandHandler("pairs",       cmd_pairs))
    app.add_handler(CommandHandler("scan",        cmd_scan))
    app.add_handler(CommandHandler("autosignal",  cmd_autosignal))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("summary",     cmd_summary))
    app.add_handler(CommandHandler("debug",       cmd_debug))
    app.add_handler(CommandHandler("history",     cmd_history))
    app.add_handler(CommandHandler("build",       cmd_build))
    app.add_handler(CommandHandler("time",        cmd_time))
    app.add_handler(CommandHandler("confidence",  cmd_confidence))
    app.add_handler(CommandHandler("balance",     cmd_balance))
    app.add_handler(CommandHandler("resume",      cmd_resume))
    app.add_handler(CommandHandler("newssid",     cmd_newssid))
    app.add_handler(CallbackQueryHandler(callback_result))

    print("[Main] Polling …")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
