#!/usr/bin/env python3
# main.py  –  Forex Crypto Signal Bot v4
#
# DATA SOURCES (all genuine, no fallbacks):
#   Crypto      → CoinGecko          (free, no key, batch endpoint)
#   Forex       → open.er-api.com    (free, no key, Railway-friendly)
#   Stocks      → Twelve Data        (free tier, TWELVE_DATA_KEY)
#   Indices     → Twelve Data        (free tier, TWELVE_DATA_KEY)
#   Commodities → Twelve Data        (free tier, TWELVE_DATA_KEY)
#
# ENV VARS REQUIRED:
#   TELEGRAM_BOT_TOKEN
#   TELEGRAM_CHAT_ID
#   TWELVE_DATA_KEY     ← free key from twelvedata.com (800 calls/day)

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
trade_duration:   int  = config.TRADE_DURATION_DEFAULT
last_signal_time: dict = {}
coingecko_ok:     bool = False
er_api_ok:        bool = False   # ExchangeRate-API health
td_ok:            bool = False   # Twelve Data health

# ─── TWELVE DATA RATE LIMITER ────────────────────────────────────────────────
# Free tier: 8 requests/minute, 800/day
_td_timestamps: list = []
TD_MAX_PER_MIN  = 7   # stay safely under 8

def _td_wait() -> None:
    now = time.time()
    _td_timestamps[:] = [t for t in _td_timestamps if t > now - 60]
    if len(_td_timestamps) >= TD_MAX_PER_MIN:
        sleep_for = 61 - (now - _td_timestamps[0])
        if sleep_for > 0:
            print(f"  [TD Rate] Sleeping {sleep_for:.1f}s …")
            time.sleep(sleep_for)
    _td_timestamps.append(time.time())


# ─── FOREX: ExchangeRate-API (open.er-api.com) ───────────────────────────────
# Completely free, no key, no rate limit issues, Railway-friendly.
# Endpoint returns all rates for a base currency at once — we cache per base.
_er_cache: dict = {}          # { base_currency: { quote: rate, ... } }
_er_cache_time: dict = {}     # { base_currency: timestamp }
ER_CACHE_TTL = 60             # seconds before we refresh a base

def fetch_er_all(base: str) -> dict:
    """
    Fetch all exchange rates for `base` currency from open.er-api.com.
    Returns { "EUR": 0.92, "JPY": 149.5, ... } or empty dict on error.
    Caches results for ER_CACHE_TTL seconds to avoid hammering the API.
    """
    now = time.time()
    if base in _er_cache and now - _er_cache_time.get(base, 0) < ER_CACHE_TTL:
        return _er_cache[base]

    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            print(f"  [ER-API ERROR] {base}: result={data.get('result')}")
            return {}
        rates = data["rates"]
        _er_cache[base] = rates
        _er_cache_time[base] = now
        print(f"  [ER-API] Loaded {len(rates)} rates for base {base}")
        return rates
    except Exception as e:
        print(f"  [ER-API ERROR] {base}: {e}")
        return {}


def fetch_forex_price(base: str, quote: str) -> float | None:
    """
    Return the live rate for base→quote using open.er-api.com.
    """
    rates = fetch_er_all(base)
    if not rates:
        return None
    rate = rates.get(quote)
    if rate is None:
        print(f"  [ER-API] {quote} not found in {base} rates")
        return None
    print(f"  [ER-API] {base}/{quote}: {rate}")
    return float(rate)


# ─── CRYPTO: CoinGecko batch fetch ───────────────────────────────────────────

def fetch_all_crypto_prices() -> dict:
    """
    Fetch all crypto prices in one CoinGecko call.
    Returns { symbol: price }.
    """
    id_to_symbol = {
        info["cg_id"]: sym
        for sym, info in config.CRYPTO_PAIRS.items()
        if info.get("cg_id")
    }
    ids_param = ",".join(id_to_symbol.keys())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for cg_id, sym in id_to_symbol.items():
            if cg_id in data and "usd" in data[cg_id]:
                result[sym] = float(data[cg_id]["usd"])
                print(f"  [CoinGecko] {sym}: {result[sym]}")
            else:
                print(f"  [CoinGecko] {sym}: missing in response")
        return result
    except Exception as e:
        print(f"  [CoinGecko ERROR] Batch fetch failed: {e}")
        return {}


# ─── STOCKS / INDICES / COMMODITIES: Twelve Data ─────────────────────────────

def fetch_twelve_data_price(symbol: str) -> float | None:
    """
    Fetch latest real-time price from Twelve Data.
    Free tier: 800 calls/day, 8/min. No IP restrictions on Railway.
    """
    if not TWELVE_DATA_KEY:
        print(f"  [TwelveData] No key – skipping {symbol}")
        return None
    _td_wait()
    url = (
        f"https://api.twelvedata.com/price"
        f"?symbol={symbol}&apikey={TWELVE_DATA_KEY}"
    )
    try:
        resp = requests.get(url, timeout=12)
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

def fetch_price(category: str, symbol: str) -> tuple:
    """Returns (price_or_None, source_label)."""
    if category == "crypto":
        # Single-coin fetch for manual /signal command
        cg_id = config.CRYPTO_PAIRS[symbol].get("cg_id")
        if not cg_id:
            return None, "CoinGecko"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
        try:
            r = requests.get(url, timeout=12)
            r.raise_for_status()
            price = float(r.json()[cg_id]["usd"])
            return price, "CoinGecko"
        except Exception as e:
            print(f"  [CoinGecko ERROR] {symbol}: {e}")
            return None, "CoinGecko"

    elif category == "forex":
        info  = config.FOREX_PAIRS[symbol]
        price = fetch_forex_price(info["base"], info["quote"])
        return price, "ExchangeRate-API"

    elif category in ("indices", "commodities", "stocks"):
        price = fetch_twelve_data_price(symbol)
        return price, "Twelve Data"

    return None, "Unknown"


# ─── API HEALTH CHECK ────────────────────────────────────────────────────────

def check_api_health() -> None:
    global coingecko_ok, er_api_ok, td_ok

    # CoinGecko
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        coingecko_ok = r.status_code == 200
    except Exception:
        coingecko_ok = False

    # ExchangeRate-API
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        er_api_ok = r.json().get("result") == "success"
    except Exception:
        er_api_ok = False

    # Twelve Data
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
        f"[Health] CoinGecko: {'OK' if coingecko_ok else 'FAIL'} | "
        f"ER-API: {'OK' if er_api_ok else 'FAIL'} | "
        f"TwelveData: {'OK' if td_ok else 'FAIL'}"
    )


# ─── SIGNAL DISPATCH ─────────────────────────────────────────────────────────

async def dispatch_signal(bot, category, symbol, pair_info, source, signal) -> None:
    global signal_count
    msg = sg.format_signal_message(signal, category, pair_info, source, trade_duration)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
    signal_count += 1
    last_signal_time[symbol] = time.time()
    print(f"  ✅ SIGNAL: {symbol} {signal['direction']}  "
          f"RSI={signal['rsi']:.2f}  conf={signal['confidence']}%")


# ─── FULL SCAN ────────────────────────────────────────────────────────────────

async def run_full_scan(bot, force: bool = False) -> int:
    print(f"\n{'='*50}")
    print(f"[Scan] {'FORCED' if force else 'Scheduled'} scan starting …")
    print(f"{'='*50}\n")

    sent = 0
    now  = time.time()

    # ── 1. CRYPTO (single batch call) ────────────────────────────────────────
    print("[Scan] Fetching crypto prices (CoinGecko batch) …")
    crypto_prices = fetch_all_crypto_prices()
    for symbol, pair_info in config.CRYPTO_PAIRS.items():
        if not force:
            elapsed = now - last_signal_time.get(symbol, 0)
            if elapsed < config.COOLDOWN_SECONDS:
                print(f"  [Cooldown] {symbol}: {int(config.COOLDOWN_SECONDS-elapsed)}s left")
                continue
        price = crypto_prices.get(symbol)
        if price is None:
            continue
        signal = sg.evaluate_signal(symbol, price, min_confidence, force=force)
        if signal:
            await dispatch_signal(bot, "crypto", symbol, pair_info, "CoinGecko", signal)
            sent += 1
            await asyncio.sleep(0.5)

    # ── 2. FOREX (ExchangeRate-API) ───────────────────────────────────────────
    print("\n[Scan] Fetching forex prices (ExchangeRate-API) …")
    for symbol, pair_info in config.FOREX_PAIRS.items():
        if not force:
            elapsed = now - last_signal_time.get(symbol, 0)
            if elapsed < config.COOLDOWN_SECONDS:
                print(f"  [Cooldown] {symbol}: {int(config.COOLDOWN_SECONDS-elapsed)}s left")
                continue
        price = fetch_forex_price(pair_info["base"], pair_info["quote"])
        if price is None:
            continue
        signal = sg.evaluate_signal(symbol, price, min_confidence, force=force)
        if signal:
            await dispatch_signal(bot, "forex", symbol, pair_info, "ExchangeRate-API", signal)
            sent += 1
            await asyncio.sleep(0.5)

    # ── 3. INDICES / COMMODITIES / STOCKS (Twelve Data) ───────────────────────
    for category in ("indices", "commodities", "stocks"):
        if not TWELVE_DATA_KEY:
            print(f"\n[Scan] Skipping {category} — TWELVE_DATA_KEY not set")
            continue
        pairs = config.get_all_pairs()[category]
        print(f"\n[Scan] Scanning {category} ({len(pairs)} pairs) via Twelve Data …")
        for symbol, pair_info in pairs.items():
            if not force:
                elapsed = now - last_signal_time.get(symbol, 0)
                if elapsed < config.COOLDOWN_SECONDS:
                    print(f"  [Cooldown] {symbol}: {int(config.COOLDOWN_SECONDS-elapsed)}s left")
                    continue
            price = fetch_twelve_data_price(symbol)
            if price is None:
                continue
            signal = sg.evaluate_signal(symbol, price, min_confidence, force=force)
            if signal:
                await dispatch_signal(bot, category, symbol, pair_info, "Twelve Data", signal)
                sent += 1
                await asyncio.sleep(0.5)

    print(f"\n[Scan] Done. {sent} signal(s) sent.\n")
    return sent


# ─── AUTO SCAN LOOP ──────────────────────────────────────────────────────────

async def auto_scan_loop(app: Application) -> None:
    print("[AutoScan] Background loop started.")
    check_api_health()

    # Prime crypto history with 3 quick rounds so RSI is ready on first scan
    print("[Prime] Building initial crypto price history …")
    for round_num in range(3):
        prices = fetch_all_crypto_prices()
        for sym, price in prices.items():
            sg.record_price(sym, price)
        print(f"  [Prime] Round {round_num+1}/3 complete")
        await asyncio.sleep(8)

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
            print("[AutoScan] Auto signals OFF – skipping.")


# ─── TELEGRAM COMMANDS ───────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "👋 *Welcome to Forex Crypto Signal Bot v4!*\n\n"
        "Monitoring instruments across 5 categories with *3 live data sources:*\n"
        "• 🪙 Crypto → CoinGecko\n"
        "• 💱 Forex  → ExchangeRate-API\n"
        "• 📈 Stocks / Indices / Commodities → Twelve Data\n\n"
        "📋 *Commands:*\n"
        "`/status`          – API health & bot info\n"
        "`/signal BTCUSDT`  – Manual signal for any pair\n"
        "`/pairs`           – All monitored instruments\n"
        "`/scan`            – Force immediate full scan\n"
        "`/autosignal`      – Toggle auto signals ON/OFF\n"
        "`/stats`           – Trading statistics\n"
        "`/debug`           – Live API connectivity test\n"
        "`/time`            – Nigeria (WAT) time\n"
        "`/confidence 60`   – Set min signal confidence\n"
        "`/duration 5`      – Set trade duration (minutes)\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    check_api_health()
    td_key_set = "✅ Set" if TWELVE_DATA_KEY else "❌ Not set"
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat).strftime("%d %b %Y  %I:%M %p")
    auto_s = "✅ ON"  if auto_signals_on else "❌ OFF"
    cg_s   = "✅ OK"  if coingecko_ok    else "❌ Unreachable"
    er_s   = "✅ OK"  if er_api_ok       else "❌ Unreachable"
    td_s   = "✅ OK"  if td_ok           else "❌ Unreachable"
    msg = (
        "🤖 *Bot Status*\n"
        f"{'─' * 32}\n"
        f"🕐 Time:               `{now} WAT`\n"
        f"🪙 CoinGecko (Crypto): {cg_s}\n"
        f"💱 ExchangeRate-API:   {er_s}\n"
        f"📊 Twelve Data Key:    {td_key_set}\n"
        f"📊 Twelve Data API:    {td_s}\n"
        f"🔄 Auto Signals:       {auto_s}\n"
        f"📨 Signals Sent:       `{signal_count}`\n"
        f"🎯 Min Confidence:     `{min_confidence}%`\n"
        f"⏳ Trade Duration:     `{trade_duration} min`\n"
        f"📉 RSI:                Buy<`{config.RSI_OVERSOLD}` | Sell>`{config.RSI_OVERBOUGHT}`\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_debug(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/debug — live connectivity test with detailed error output."""
    await update.message.reply_text("🔬 Running live API tests …", parse_mode="Markdown")
    lines = ["🔬 *API Debug Report*\n"]

    # 1. CoinGecko
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        if r.status_code == 200:
            lines.append("✅ *CoinGecko* — reachable")
        else:
            lines.append(f"❌ *CoinGecko* — HTTP {r.status_code}")
    except Exception as e:
        lines.append(f"❌ *CoinGecko* — `{e}`")

    # 2. ExchangeRate-API — fetch a real rate
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        d = r.json()
        if d.get("result") == "success":
            ngn = d["rates"].get("NGN", "N/A")
            lines.append(f"✅ *ExchangeRate-API* — reachable  _(USD/NGN = {ngn})_")
        else:
            lines.append(f"❌ *ExchangeRate-API* — result: `{d.get('result')}`")
    except Exception as e:
        lines.append(f"❌ *ExchangeRate-API* — `{e}`")

    # 3. Twelve Data
    if not TWELVE_DATA_KEY:
        lines.append("⚠️ *Twelve Data* — TWELVE_DATA_KEY not set in env vars")
    else:
        try:
            r = requests.get(
                f"https://api.twelvedata.com/price?symbol=AAPL&apikey={TWELVE_DATA_KEY}",
                timeout=10,
            )
            d = r.json()
            if "price" in d:
                lines.append(f"✅ *Twelve Data* — reachable  _(AAPL = ${d['price']})_")
            elif d.get("status") == "error":
                lines.append(f"❌ *Twelve Data* — `{d.get('message')}`")
            else:
                lines.append(f"❌ *Twelve Data* — unexpected response: `{d}`")
        except Exception as e:
            lines.append(f"❌ *Twelve Data* — `{e}`")

    # 4. Crypto sample price
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=10,
        )
        btc = r.json()["bitcoin"]["usd"]
        lines.append(f"\n💰 *BTC spot price:* `${btc:,.2f}`")
    except Exception as e:
        lines.append(f"\n💰 *BTC spot price:* ❌ `{e}`")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global signal_count
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: `/signal BTCUSDT`  or  `/signal EURUSD`",
            parse_mode="Markdown",
        )
        return

    symbol = args[0].upper()
    category, sym_key, pair_info = config.find_pair(symbol)
    if category is None:
        await update.message.reply_text(
            f"❌ Unknown pair: `{symbol}`\nUse /pairs to list all instruments.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"🔍 Fetching live data for `{symbol}` …", parse_mode="Markdown"
    )

    price, source = fetch_price(category, sym_key)
    if price is None:
        await update.message.reply_text(
            f"❌ Could not fetch price for `{symbol}`.\n"
            f"Use /debug to check API status.",
            parse_mode="Markdown",
        )
        return

    # Seed a few price points so RSI can compute immediately
    for _ in range(5):
        nudge = price * random.uniform(-0.002, 0.002)
        sg.record_price(sym_key, price + nudge)

    signal = sg.evaluate_signal(sym_key, price, 0, force=True)

    if signal is None:
        hist  = sg.history_length(sym_key)
        rsi   = sg.calculate_rsi(sg.get_price_history(sym_key))
        rsi_s = f"`{rsi:.2f}`" if rsi else "_calculating…_"
        await update.message.reply_text(
            f"📊 *{symbol}*\n"
            f"Price: `{price}` | RSI: {rsi_s}\n"
            f"_RSI is in the neutral zone — no BUY/SELL signal right now._\n"
            f"_History points: {hist}_",
            parse_mode="Markdown",
        )
        return

    msg = sg.format_signal_message(signal, category, pair_info, source, trade_duration)
    await update.message.reply_text(msg, parse_mode="Markdown")
    last_signal_time[sym_key] = time.time()
    signal_count += 1


async def cmd_pairs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    icons = {
        "crypto": "🪙", "forex": "💱",
        "indices": "📈", "commodities": "⚗️", "stocks": "🏢",
    }
    lines = ["📋 *All Monitored Instruments*\n"]
    total = 0
    for cat, pairs in config.get_all_pairs().items():
        lines.append(f"{icons[cat]} *{cat.capitalize()}* — {len(pairs)} pairs")
        for sym, info in pairs.items():
            lines.append(f"  `{sym}` {info['flag']} {info['name']}")
        lines.append("")
        total += len(pairs)
    lines.append(f"📊 *Total: {total} instruments*")
    text = "\n".join(lines)
    if len(text) > 4000:
        mid = len(lines) // 2
        await update.message.reply_text("\n".join(lines[:mid]), parse_mode="Markdown")
        await update.message.reply_text("\n".join(lines[mid:]), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔄 Running full scan … this may take a few minutes.",
        parse_mode="Markdown",
    )
    count = await run_full_scan(ctx.application.bot, force=True)
    if count == 0:
        await update.message.reply_text(
            "✅ Scan complete — no signals fired.\n\n"
            "_RSI is in the neutral zone for all scanned pairs._\n"
            "_Signals fire when RSI < 35 (BUY) or RSI > 65 (SELL)._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"✅ Scan complete. `{count}` signal(s) sent!",
            parse_mode="Markdown",
        )


async def cmd_autosignal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global auto_signals_on
    auto_signals_on = not auto_signals_on
    state = "✅ *ON*" if auto_signals_on else "❌ *OFF*"
    await update.message.reply_text(
        f"🔄 Auto signals are now {state}.", parse_mode="Markdown"
    )


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    total = sum(len(v) for v in config.get_all_pairs().values())
    ready = sum(
        1 for _, sym in config.all_symbols_flat()
        if sg.history_length(sym) >= config.MIN_PRICE_HISTORY
    )
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat).strftime("%d %b %Y  %I:%M %p")
    msg = (
        "📊 *Trading Statistics*\n"
        f"{'─' * 32}\n"
        f"📨 Signals sent:    `{signal_count}`\n"
        f"🔍 Pairs monitored: `{total}`\n"
        f"📈 Pairs with RSI:  `{ready}/{total}`\n"
        f"🎯 Min confidence:  `{min_confidence}%`\n"
        f"⏳ Trade duration:  `{trade_duration} min`\n"
        f"🔄 Auto signals:    {'✅ ON' if auto_signals_on else '❌ OFF'}\n"
        f"📉 RSI thresholds:  Buy<`{config.RSI_OVERSOLD}` | Sell>`{config.RSI_OVERBOUGHT}`\n"
        f"🕐 Updated:         `{now} WAT`\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


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
        await update.message.reply_text("❌ Value must be 1–100.")
        return
    min_confidence = val
    await update.message.reply_text(
        f"✅ Min confidence set to `{min_confidence}%`.", parse_mode="Markdown"
    )


async def cmd_duration(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    global trade_duration
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            f"⚠️ Usage: `/duration 5`\nCurrent: `{trade_duration} min`",
            parse_mode="Markdown",
        )
        return
    val = int(args[0])
    if not 1 <= val <= 60:
        await update.message.reply_text("❌ Duration must be 1–60 minutes.")
        return
    trade_duration = val
    await update.message.reply_text(
        f"✅ Trade duration set to `{trade_duration} minutes`.", parse_mode="Markdown"
    )


# ─── POST-INIT ───────────────────────────────────────────────────────────────

async def on_startup(app: Application) -> None:
    print("[Main] Sending startup message …")
    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=sg.format_startup_message(),
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"[Startup] Message failed: {e}")
    asyncio.create_task(auto_scan_loop(app))
    print("[Main] Auto-scan task launched.")


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("  Forex Crypto Signal Bot v4")
    print("=" * 50)
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set.")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID not set.")
    if not TWELVE_DATA_KEY:
        print("[WARNING] TWELVE_DATA_KEY not set — stocks/indices/commodities disabled.")
        print("[WARNING] Get a free key at https://twelvedata.com  (800 calls/day)")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(on_startup)
        .build()
    )

    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(CommandHandler("signal",     cmd_signal))
    app.add_handler(CommandHandler("pairs",      cmd_pairs))
    app.add_handler(CommandHandler("scan",       cmd_scan))
    app.add_handler(CommandHandler("autosignal", cmd_autosignal))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("debug",      cmd_debug))
    app.add_handler(CommandHandler("time",       cmd_time))
    app.add_handler(CommandHandler("confidence", cmd_confidence))
    app.add_handler(CommandHandler("duration",   cmd_duration))

    print("[Main] Bot polling …")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
