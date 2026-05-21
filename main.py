#!/usr/bin/env python3
# main.py  –  Forex Crypto Signal Bot v10
#
# DATA SOURCES:
#   Crypto  → CoinGecko          (free, no key)
#   Forex   → open.er-api.com    (free, no key)
#   Stocks / Indices / Commodities → Twelve Data (TWELVE_DATA_KEY)
#
# KEY CHANGES vs v9:
#   - OTC pairs completely removed
#   - No deduplication — every pair evaluated independently
#   - Pairs shuffled each scan so different pairs signal each time
#   - MAX_SIGNALS_PER_SCAN raised to 5
#   - /build command: fetches history immediately without waiting
#   - /scan uses force=True — bypasses cooldowns always

import asyncio
import os
import random
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
import signal_generator as sg

# ─── ENV ─────────────────────────────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TWELVE_DATA_KEY  = os.getenv("TWELVE_DATA_KEY", "").strip().strip('"').strip("'")

# ─── RUNTIME STATE ───────────────────────────────────────────────────────────
auto_signals_on:  bool = True
signal_count:     int  = 0
min_confidence:   int  = config.CONFIDENCE_DEFAULT
last_signal_time: dict = {}
coingecko_ok:     bool = False
er_api_ok:        bool = False
td_ok:            bool = False

# ─── TWELVE DATA RATE LIMITER ────────────────────────────────────────────────
_td_timestamps: list = []
TD_MAX_PER_MIN  = 7

def _td_wait() -> None:
    now = time.time()
    _td_timestamps[:] = [t for t in _td_timestamps if t > now - 60]
    if len(_td_timestamps) >= TD_MAX_PER_MIN:
        sleep_for = 61 - (now - _td_timestamps[0])
        if sleep_for > 0:
            print(f"  [TD Rate] Sleeping {sleep_for:.1f}s …")
            time.sleep(sleep_for)
    _td_timestamps.append(time.time())


# ─── FOREX: open.er-api.com ───────────────────────────────────────────────────
_er_cache:      dict = {}
_er_cache_time: dict = {}
ER_CACHE_TTL = 60

def fetch_er_all(base: str) -> dict:
    now = time.time()
    if base in _er_cache and now - _er_cache_time.get(base, 0) < ER_CACHE_TTL:
        return _er_cache[base]
    try:
        resp = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=12)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            return {}
        _er_cache[base] = data["rates"]
        _er_cache_time[base] = now
        return data["rates"]
    except Exception as e:
        print(f"  [ER-API ERROR] {base}: {e}")
        return {}

def fetch_forex_price(base: str, quote: str) -> float | None:
    rates = fetch_er_all(base)
    rate  = rates.get(quote)
    if rate is None:
        return None
    print(f"  [ER-API] {base}/{quote}: {rate}")
    return float(rate)


# ─── CRYPTO: CoinGecko batch ─────────────────────────────────────────────────

def fetch_all_crypto_prices() -> dict:
    """Single API call fetches all crypto prices."""
    id_to_symbols: dict[str, list] = {}
    for sym, info in config.CRYPTO_PAIRS.items():
        cg_id = info.get("cg_id")
        if cg_id:
            id_to_symbols.setdefault(cg_id, []).append(sym)

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={','.join(id_to_symbols)}&vs_currencies=usd"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for cg_id, symbols in id_to_symbols.items():
            if cg_id in data and "usd" in data[cg_id]:
                price = float(data[cg_id]["usd"])
                for sym in symbols:
                    result[sym] = price
        return result
    except Exception as e:
        print(f"  [CoinGecko ERROR] {e}")
        return {}


# ─── TWELVE DATA ─────────────────────────────────────────────────────────────

def fetch_twelve_data_price(symbol: str) -> float | None:
    if not TWELVE_DATA_KEY:
        return None
    _td_wait()
    try:
        resp = requests.get(
            f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_KEY}",
            timeout=12,
        )
        resp.raise_for_status()
        data = resp.json()
        if "price" not in data:
            print(f"  [TwelveData ERROR] {symbol}: {data.get('message', data)}")
            return None
        price = float(data["price"])
        print(f"  [TwelveData] {symbol}: {price}")
        return price
    except Exception as e:
        print(f"  [TwelveData ERROR] {symbol}: {e}")
        return None


# ─── PRICE DISPATCHER ────────────────────────────────────────────────────────

def fetch_price(category: str, symbol: str, pair_info: dict) -> tuple:
    if category == "crypto":
        cg_id = pair_info.get("cg_id")
        if not cg_id:
            return None, "CoinGecko"
        try:
            r = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd",
                timeout=12,
            )
            price = float(r.json()[cg_id]["usd"])
            return price, "CoinGecko"
        except Exception as e:
            print(f"  [CoinGecko ERROR] {symbol}: {e}")
            return None, "CoinGecko"

    elif category == "forex":
        price = fetch_forex_price(pair_info["base"], pair_info["quote"])
        return price, "ExchangeRate-API"

    elif category in ("indices", "commodities", "stocks"):
        price = fetch_twelve_data_price(symbol)
        return price, "Twelve Data"

    return None, "Unknown"


# ─── API HEALTH ──────────────────────────────────────────────────────────────

def check_api_health() -> None:
    global coingecko_ok, er_api_ok, td_ok
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        coingecko_ok = r.status_code == 200
    except Exception:
        coingecko_ok = False
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        er_api_ok = r.json().get("result") == "success"
    except Exception:
        er_api_ok = False
    if TWELVE_DATA_KEY:
        try:
            r = requests.get(
                f"https://api.twelvedata.com/price?symbol=AAPL&apikey={TWELVE_DATA_KEY}",
                timeout=10,
            )
            td_ok = "price" in r.json()
        except Exception:
            td_ok = False
    else:
        td_ok = False
    print(
        f"[Health] CoinGecko={'OK' if coingecko_ok else 'FAIL'} | "
        f"ER-API={'OK' if er_api_ok else 'FAIL'} | "
        f"TwelveData={'OK' if td_ok else 'FAIL'}"
    )


# ─── SIGNAL DISPATCH ─────────────────────────────────────────────────────────

async def dispatch_signal(
    bot, category, symbol, pair_info, source, signal,
    manual: bool = False,
) -> bool:
    """
    Send a signal. Returns True if sent.
    manual=False → blocked when auto_signals_on is False.
    manual=True  → always sends (/scan and /signal commands).
    """
    if not manual and not auto_signals_on:
        print(f"  [BLOCKED] {symbol}: auto signals OFF")
        return False

    global signal_count
    msg = sg.format_signal_message(signal, category, pair_info, source)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
    signal_count += 1
    last_signal_time[symbol] = time.time()
    print(
        f"  ✅ SIGNAL: {symbol} {signal['direction']}  "
        f"score={signal['score']}/5  conf={signal['confidence']}%  "
        f"dur={signal['duration']}min"
    )
    return True


# ─── FULL SCAN ────────────────────────────────────────────────────────────────

async def run_full_scan(bot, force: bool = False, manual: bool = False) -> int:
    """
    Scan all pairs. Pairs are SHUFFLED before each scan so different
    instruments surface as signals each time instead of always the same ones.

    force=True  → bypass per-pair cooldowns (used by /scan).
    manual=True → send signals even when auto_signals_on is OFF.
    """
    if not manual and not auto_signals_on:
        print("[Scan] Auto signals OFF — scan blocked.")
        return 0

    print(f"\n{'='*50}")
    print(f"[Scan] {'MANUAL' if manual else 'Scheduled'} scan …")
    print(f"{'='*50}\n")

    sent   = 0
    now_ts = time.time()

    # ── 1. CRYPTO ──────────────────────────────────────────────────────────────
    print("[Scan] Fetching crypto prices (CoinGecko batch) …")
    crypto_prices = fetch_all_crypto_prices()
    crypto_items  = list(config.CRYPTO_PAIRS.items())
    random.shuffle(crypto_items)  # shuffle for variety

    for symbol, pair_info in crypto_items:
        if sent >= config.MAX_SIGNALS_PER_SCAN:
            break
        if not force and now_ts - last_signal_time.get(symbol, 0) < config.COOLDOWN_SECONDS:
            continue
        price = crypto_prices.get(symbol)
        if price is None:
            continue
        signal = sg.evaluate_signal(symbol, price, min_confidence)
        if signal:
            ok = await dispatch_signal(bot, "crypto", symbol, pair_info, "CoinGecko", signal, manual=manual)
            if ok:
                sent += 1
                await asyncio.sleep(1)

    # ── 2. FOREX ───────────────────────────────────────────────────────────────
    if sent < config.MAX_SIGNALS_PER_SCAN:
        print("\n[Scan] Fetching forex prices (ExchangeRate-API) …")
        forex_items = list(config.FOREX_PAIRS.items())
        random.shuffle(forex_items)

        for symbol, pair_info in forex_items:
            if sent >= config.MAX_SIGNALS_PER_SCAN:
                break
            if not force and now_ts - last_signal_time.get(symbol, 0) < config.COOLDOWN_SECONDS:
                continue
            price = fetch_forex_price(pair_info["base"], pair_info["quote"])
            if price is None:
                continue
            signal = sg.evaluate_signal(symbol, price, min_confidence)
            if signal:
                ok = await dispatch_signal(bot, "forex", symbol, pair_info, "ExchangeRate-API", signal, manual=manual)
                if ok:
                    sent += 1
                    await asyncio.sleep(1)

    # ── 3. INDICES / COMMODITIES / STOCKS ──────────────────────────────────────
    for category in ("indices", "commodities", "stocks"):
        if sent >= config.MAX_SIGNALS_PER_SCAN:
            break
        if not TWELVE_DATA_KEY:
            print(f"\n[Scan] Skipping {category} — TWELVE_DATA_KEY not set")
            continue
        pairs      = config.get_all_pairs()[category]
        pair_items = list(pairs.items())
        random.shuffle(pair_items)
        print(f"\n[Scan] {category} ({len(pairs)} pairs) …")

        for symbol, pair_info in pair_items:
            if sent >= config.MAX_SIGNALS_PER_SCAN:
                break
            if not force and now_ts - last_signal_time.get(symbol, 0) < config.COOLDOWN_SECONDS:
                continue
            price = fetch_twelve_data_price(symbol)
            if price is None:
                continue
            signal = sg.evaluate_signal(symbol, price, min_confidence)
            if signal:
                ok = await dispatch_signal(bot, category, symbol, pair_info, "Twelve Data", signal, manual=manual)
                if ok:
                    sent += 1
                    await asyncio.sleep(1)

    print(f"\n[Scan] Done. {sent} signal(s) sent.\n")
    return sent


# ─── AUTO SCAN LOOP ──────────────────────────────────────────────────────────

async def auto_scan_loop(app: Application) -> None:
    print("[AutoScan] Loop started.")
    check_api_health()
    while True:
        interval = random.randint(
            config.SCAN_INTERVAL_MIN * 60,
            config.SCAN_INTERVAL_MAX * 60,
        )
        print(f"[AutoScan] Next scan in {interval//60}m {interval%60}s")
        await asyncio.sleep(interval)
        if auto_signals_on:
            await run_full_scan(app.bot)
        else:
            print("[AutoScan] OFF – skipping.")


# ─── COMMANDS ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    total = sum(len(v) for v in config.get_all_pairs().values())
    await update.message.reply_text(
        "👋 *Forex Crypto Signal Bot v10*\n\n"
        f"🔬 *5-Indicator Engine* (RSI · Stoch · MACD · BB · EMA)\n"
        f"_Signals fire when {config.MIN_SCORE}/5 indicators align_\n\n"
        f"📊 *{total} real market pairs* across 5 categories\n\n"
        "📋 *Commands:*\n"
        "`/build`          – Build history now (no waiting)\n"
        "`/scan`           – Force scan for signals\n"
        "`/history`        – Check indicator readiness\n"
        "`/status`         – API health\n"
        "`/signal EURUSD`  – Check one pair manually\n"
        "`/pairs`          – All monitored pairs\n"
        "`/autosignal`     – Toggle auto signals ON/OFF\n"
        "`/stats`          – Statistics\n"
        "`/debug`          – Live API test\n"
        "`/time`           – Nigeria time\n"
        "`/confidence 60`  – Min signal confidence\n",
        parse_mode="Markdown",
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    check_api_health()
    msg = sg.format_status_message(
        auto_signals_on, signal_count,
        coingecko_ok, er_api_ok, td_ok,
        min_confidence,
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_debug(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔬 Testing APIs …")
    lines = ["🔬 *API Debug Report*\n"]
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        lines.append("✅ *CoinGecko* — reachable" if r.status_code == 200
                     else f"❌ *CoinGecko* — HTTP {r.status_code}")
    except Exception as e:
        lines.append(f"❌ *CoinGecko* — `{e}`")
    try:
        r   = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        d   = r.json()
        ngn = d.get("rates", {}).get("NGN", "N/A")
        lines.append(f"✅ *ExchangeRate-API* — reachable  _(USD/NGN ≈ {ngn})_"
                     if d.get("result") == "success"
                     else f"❌ *ExchangeRate-API* — `{d.get('result')}`")
    except Exception as e:
        lines.append(f"❌ *ExchangeRate-API* — `{e}`")
    if not TWELVE_DATA_KEY:
        lines.append("⚠️ *Twelve Data* — TWELVE\\_DATA\\_KEY not set")
    else:
        try:
            r = requests.get(
                f"https://api.twelvedata.com/price?symbol=AAPL&apikey={TWELVE_DATA_KEY}",
                timeout=10,
            )
            d = r.json()
            lines.append(f"✅ *Twelve Data* — reachable  _(AAPL = ${d['price']})_"
                         if "price" in d else f"❌ *Twelve Data* — `{d.get('message', d)}`")
        except Exception as e:
            lines.append(f"❌ *Twelve Data* — `{e}`")
    try:
        r   = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=10,
        )
        btc = r.json()["bitcoin"]["usd"]
        lines.append(f"\n💰 *BTC spot:* `${btc:,.2f}`")
    except Exception as e:
        lines.append(f"\n💰 *BTC spot:* ❌ `{e}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    icons  = {"crypto": "🪙", "forex": "💱", "indices": "📈",
              "commodities": "⚗️", "stocks": "🏢"}
    needed = config.MIN_PRICE_HISTORY
    lines  = [f"📈 *Indicator History Progress*\n_Need {needed} points per pair_\n"]
    total_ready = total_pairs = 0
    for cat, pairs in config.get_all_pairs().items():
        ready = sum(1 for s in pairs if sg.history_length(s) >= needed)
        total_ready += ready
        total_pairs += len(pairs)
        lines.append(f"{icons[cat]} *{cat.capitalize()}*: `{ready}/{len(pairs)}` ready")
    lines.append(f"\n📊 *Total: {total_ready}/{total_pairs} pairs ready*")
    lines.append(f"\n_Run /build to fetch all history immediately._")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /build — fetches real price rounds back-to-back to build indicator
    history quickly. Each round = 1 real price point per pair.
    Stops early once all pairs reach MIN_PRICE_HISTORY. No signals sent.
    """
    needed  = config.MIN_PRICE_HISTORY
    total   = sum(len(v) for v in config.get_all_pairs().values())
    already = sum(1 for _, sym in config.all_symbols_flat()
                  if sg.history_length(sym) >= needed)

    if already == total:
        await update.message.reply_text(
            f"✅ All *{total}* pairs already have full history!\n"
            f"Run /scan to check for signals.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"⚡ *Building price history …*\n\n"
        f"_Fetching {needed} rounds of real prices for all pairs._\n"
        f"_Already ready: {already}/{total} pairs_\n"
        f"_You will get a message when done._",
        parse_mode="Markdown",
    )

    bot = ctx.application.bot
    for round_num in range(1, needed + 1):
        # Crypto batch
        crypto_prices = fetch_all_crypto_prices()
        for sym, price in crypto_prices.items():
            sg.record_price(sym, price)

        # Forex
        for symbol, pair_info in config.FOREX_PAIRS.items():
            price = fetch_forex_price(pair_info["base"], pair_info["quote"])
            if price:
                sg.record_price(symbol, price)

        # Twelve Data
        if TWELVE_DATA_KEY:
            for category in ("indices", "commodities", "stocks"):
                for symbol in config.get_all_pairs()[category]:
                    price = fetch_twelve_data_price(symbol)
                    if price:
                        sg.record_price(symbol, price)

        ready_now = sum(1 for _, sym in config.all_symbols_flat()
                        if sg.history_length(sym) >= needed)
        print(f"[Build] Round {round_num}/{needed} — {ready_now}/{total} pairs ready")

        if ready_now >= total:
            break

        if round_num % 5 == 0:
            try:
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⏳ *Building …* Round {round_num}/{needed} — `{ready_now}/{total}` ready",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

        await asyncio.sleep(3)

    final = sum(1 for _, sym in config.all_symbols_flat()
                if sg.history_length(sym) >= needed)
    await update.message.reply_text(
        f"✅ *History build complete!*\n\n"
        f"📊 *{final}/{total}* pairs ready.\n\n"
        f"_Run /scan now to check for signals._",
        parse_mode="Markdown",
    )


async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    needed      = config.MIN_PRICE_HISTORY
    total       = sum(len(v) for v in config.get_all_pairs().values())
    hist_ready  = sum(1 for _, sym in config.all_symbols_flat()
                      if sg.history_length(sym) >= needed)
    await update.message.reply_text(
        f"🔄 *Running full scan …*\n"
        f"_Pairs ready: {hist_ready}/{total}_\n"
        f"_Cooldowns bypassed. Signals fire when {config.MIN_SCORE}/5 align._",
        parse_mode="Markdown",
    )
    count = await run_full_scan(ctx.application.bot, force=True, manual=True)
    if count == 0:
        not_ready = total - hist_ready
        msg = f"✅ *Scan complete — no signals fired.*\n\n"
        if not_ready > 0:
            msg += f"⏳ *{not_ready}* pairs still need history. Run /build first.\n\n"
        if hist_ready > 0:
            msg += (
                f"📊 *{hist_ready}* pairs were evaluated.\n"
                f"_All RSI in neutral zone or < {config.MIN_SCORE}/5 indicators aligned._\n"
                f"_This means market conditions aren't right — correct behaviour._"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"✅ *Scan complete.* `{count}` signal(s) sent!", parse_mode="Markdown"
        )


async def cmd_autosignal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global auto_signals_on
    auto_signals_on = not auto_signals_on
    if auto_signals_on:
        msg = (
            "✅ *Auto signals are now ON*\n"
            f"_Scanning every {config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX} min, "
            f"up to {config.MAX_SIGNALS_PER_SCAN} signals per scan._"
        )
    else:
        msg = (
            "❌ *Auto signals are now OFF*\n"
            "_No automatic signals._\n"
            "_Use /scan to trigger manually._"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    total = sum(len(v) for v in config.get_all_pairs().values())
    ready = sum(1 for _, sym in config.all_symbols_flat()
                if sg.history_length(sym) >= config.MIN_PRICE_HISTORY)
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat).strftime("%d %b %Y  %I:%M %p")
    await update.message.reply_text(
        "📊 *Statistics*\n"
        f"{'─'*32}\n"
        f"📨 Signals sent:    `{signal_count}`\n"
        f"🔍 Pairs monitored: `{total}`\n"
        f"📈 Pairs with data: `{ready}/{total}`\n"
        f"🎯 Min confidence:  `{min_confidence}%`\n"
        f"🔬 Score required:  `{config.MIN_SCORE}/5`\n"
        f"🔄 Auto signals:    {'✅ ON' if auto_signals_on else '❌ OFF'}\n"
        f"🚦 Max/scan:        `{config.MAX_SIGNALS_PER_SCAN}`\n"
        f"🕐 Updated:         `{now} WAT`\n",
        parse_mode="Markdown",
    )


async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global signal_count
    args = ctx.args
    if not args:
        await update.message.reply_text("⚠️ Usage: `/signal BTCUSDT`", parse_mode="Markdown")
        return
    symbol = args[0].upper()
    category, sym_key, pair_info = config.find_pair(symbol)
    if category is None:
        await update.message.reply_text(
            f"❌ Unknown: `{symbol}`\nUse /pairs to see all.", parse_mode="Markdown"
        )
        return
    await update.message.reply_text(f"🔍 Fetching `{symbol}` …", parse_mode="Markdown")
    price, source = fetch_price(category, sym_key, pair_info)
    if price is None:
        await update.message.reply_text(
            f"❌ Could not fetch `{symbol}`. Use /debug.", parse_mode="Markdown"
        )
        return
    sg.record_price(sym_key, price)
    hist = sg.history_length(sym_key)
    if hist < config.MIN_PRICE_HISTORY:
        await update.message.reply_text(
            f"📊 *{symbol}* | Price: `{price}`\n"
            f"History: `{hist}/{config.MIN_PRICE_HISTORY}` points\n"
            f"_Run /build to fill history quickly._",
            parse_mode="Markdown",
        )
        return
    signal = sg.evaluate_signal(sym_key, price, 0, force=True)
    if signal is None:
        rsi = sg.calculate_rsi(sg.get_price_history(sym_key))
        rsi_s = f"`{rsi:.2f}`" if rsi else "_N/A_"
        await update.message.reply_text(
            f"📊 *{symbol}* | Price: `{price}` | RSI: {rsi_s}\n"
            f"_Neutral zone or < {config.MIN_SCORE}/5 indicators aligned._\n"
            f"_No signal right now._",
            parse_mode="Markdown",
        )
        return
    msg = sg.format_signal_message(signal, category, pair_info, source)
    await update.message.reply_text(msg, parse_mode="Markdown")
    last_signal_time[sym_key] = time.time()
    signal_count += 1


async def cmd_pairs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    icons = {"crypto": "🪙", "forex": "💱", "indices": "📈",
             "commodities": "⚗️", "stocks": "🏢"}
    lines = ["📋 *All Monitored Pairs*\n"]
    total = 0
    for cat, pairs in config.get_all_pairs().items():
        lines.append(f"{icons[cat]} *{cat.capitalize()}* — {len(pairs)} pairs")
        for sym, info in pairs.items():
            lines.append(f"  `{sym}` {info['flag']} {info['name']}")
        lines.append("")
        total += len(pairs)
    lines.append(f"📊 *Total: {total} pairs*")
    text = "\n".join(lines)
    if len(text) > 4000:
        mid = len(lines) // 2
        await update.message.reply_text("\n".join(lines[:mid]), parse_mode="Markdown")
        await update.message.reply_text("\n".join(lines[mid:]), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat)
    await update.message.reply_text(
        f"🕐 *Nigeria Time (WAT / UTC+1)*\n"
        f"`{now.strftime('%A, %d %B %Y  %I:%M:%S %p')}`",
        parse_mode="Markdown",
    )


async def cmd_confidence(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global min_confidence
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            f"⚠️ Usage: `/confidence 60`\nCurrent: `{min_confidence}%`",
            parse_mode="Markdown",
        )
        return
    val = int(args[0])
    if not 1 <= val <= 100:
        await update.message.reply_text("❌ Must be 1–100.")
        return
    min_confidence = val
    await update.message.reply_text(
        f"✅ Min confidence: `{min_confidence}%`", parse_mode="Markdown"
    )


# ─── POST-INIT ───────────────────────────────────────────────────────────────

async def on_startup(app: Application) -> None:
    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=sg.format_startup_message(),
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"[Startup] {e}")
    asyncio.create_task(auto_scan_loop(app))


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("  Forex Crypto Signal Bot v10")
    print("=" * 50)
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set.")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID not set.")
    if not TWELVE_DATA_KEY:
        print("[WARNING] TWELVE_DATA_KEY not set — stocks/indices/commodities disabled.")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(on_startup)
        .build()
    )
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("signal",      cmd_signal))
    app.add_handler(CommandHandler("pairs",       cmd_pairs))
    app.add_handler(CommandHandler("scan",        cmd_scan))
    app.add_handler(CommandHandler("autosignal",  cmd_autosignal))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("debug",       cmd_debug))
    app.add_handler(CommandHandler("history",     cmd_history))
    app.add_handler(CommandHandler("build",       cmd_build))
    app.add_handler(CommandHandler("time",        cmd_time))
    app.add_handler(CommandHandler("confidence",  cmd_confidence))

    print("[Main] Polling …")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
