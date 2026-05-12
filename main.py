#!/usr/bin/env python3
# main.py  –  Forex Crypto Signal Bot v5
#
# KEY FIXES vs v4:
#   - Removed ALL artificial price seeding (was the root cause of 30+ signals)
#   - MAX_SIGNALS_PER_SCAN: hard cap of 3 signals per scan cycle
#   - History builds naturally across real scan cycles only
#   - /signal command shows honest RSI without fake nudges
#   - /scan now shows per-pair RSI progress so you can see history building

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
er_api_ok:        bool = False
td_ok:            bool = False

# Hard cap: never send more than this many signals in one scan cycle.
# Prevents burst-sending when many pairs hit RSI threshold simultaneously.
MAX_SIGNALS_PER_SCAN = 3

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


# ─── FOREX: open.er-api.com (free, no key) ───────────────────────────────────
_er_cache:      dict = {}
_er_cache_time: dict = {}
ER_CACHE_TTL = 60  # seconds

def fetch_er_all(base: str) -> dict:
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
    id_to_symbol = {
        info["cg_id"]: sym
        for sym, info in config.CRYPTO_PAIRS.items()
        if info.get("cg_id")
    }
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={','.join(id_to_symbol)}&vs_currencies=usd"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for cg_id, sym in id_to_symbol.items():
            if cg_id in data and "usd" in data[cg_id]:
                result[sym] = float(data[cg_id]["usd"])
        return result
    except Exception as e:
        print(f"  [CoinGecko ERROR] {e}")
        return {}


# ─── STOCKS / INDICES / COMMODITIES: Twelve Data ─────────────────────────────

def fetch_twelve_data_price(symbol: str) -> float | None:
    if not TWELVE_DATA_KEY:
        return None
    _td_wait()
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_KEY}"
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
    if category == "crypto":
        cg_id = config.CRYPTO_PAIRS[symbol].get("cg_id")
        if not cg_id:
            return None, "CoinGecko"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
        try:
            r = requests.get(url, timeout=12)
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
    """
    Scan all pairs. Records prices into history on every call.
    Only sends a signal when RSI genuinely crosses a threshold
    based on accumulated REAL price history.

    Hard cap: MAX_SIGNALS_PER_SCAN signals per scan cycle.
    """
    print(f"\n{'='*50}")
    print(f"[Scan] {'FORCED' if force else 'Scheduled'} scan starting …")
    print(f"{'='*50}\n")

    sent      = 0
    now_ts    = time.time()

    # ── 1. CRYPTO ─────────────────────────────────────────────────────────────
    print("[Scan] Fetching crypto prices (CoinGecko batch) …")
    crypto_prices = fetch_all_crypto_prices()

    for symbol, pair_info in config.CRYPTO_PAIRS.items():
        if sent >= MAX_SIGNALS_PER_SCAN:
            break
        if not force:
            elapsed = now_ts - last_signal_time.get(symbol, 0)
            if elapsed < config.COOLDOWN_SECONDS:
                continue

        price = crypto_prices.get(symbol)
        if price is None:
            continue

        signal = sg.evaluate_signal(symbol, price, min_confidence, force=False)
        if signal:
            await dispatch_signal(bot, "crypto", symbol, pair_info, "CoinGecko", signal)
            sent += 1
            await asyncio.sleep(1)

    # ── 2. FOREX ──────────────────────────────────────────────────────────────
    if sent < MAX_SIGNALS_PER_SCAN:
        print("\n[Scan] Fetching forex prices (ExchangeRate-API) …")
        for symbol, pair_info in config.FOREX_PAIRS.items():
            if sent >= MAX_SIGNALS_PER_SCAN:
                break
            if not force:
                elapsed = now_ts - last_signal_time.get(symbol, 0)
                if elapsed < config.COOLDOWN_SECONDS:
                    continue

            price = fetch_forex_price(pair_info["base"], pair_info["quote"])
            if price is None:
                continue

            signal = sg.evaluate_signal(symbol, price, min_confidence, force=False)
            if signal:
                await dispatch_signal(bot, "forex", symbol, pair_info, "ExchangeRate-API", signal)
                sent += 1
                await asyncio.sleep(1)

    # ── 3. INDICES / COMMODITIES / STOCKS ─────────────────────────────────────
    for category in ("indices", "commodities", "stocks"):
        if sent >= MAX_SIGNALS_PER_SCAN:
            break
        if not TWELVE_DATA_KEY:
            print(f"\n[Scan] Skipping {category} — TWELVE_DATA_KEY not set")
            continue

        pairs = config.get_all_pairs()[category]
        print(f"\n[Scan] Scanning {category} ({len(pairs)} pairs) via Twelve Data …")

        for symbol, pair_info in pairs.items():
            if sent >= MAX_SIGNALS_PER_SCAN:
                break
            if not force:
                elapsed = now_ts - last_signal_time.get(symbol, 0)
                if elapsed < config.COOLDOWN_SECONDS:
                    continue

            price = fetch_twelve_data_price(symbol)
            if price is None:
                continue

            signal = sg.evaluate_signal(symbol, price, min_confidence, force=False)
            if signal:
                await dispatch_signal(bot, category, symbol, pair_info, "Twelve Data", signal)
                sent += 1
                await asyncio.sleep(1)

    print(f"\n[Scan] Done. {sent} signal(s) sent.\n")
    return sent


# ─── AUTO SCAN LOOP ──────────────────────────────────────────────────────────

async def auto_scan_loop(app: Application) -> None:
    """
    Runs a scan every 10–12 minutes.
    Prices accumulate in history naturally across cycles.
    After ~15 cycles (~2.5 hrs) most pairs will have full RSI history.
    """
    print("[AutoScan] Background loop started.")
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
            print("[AutoScan] Auto signals OFF – price history still updated next cycle.")


# ─── TELEGRAM COMMANDS ───────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "👋 *Welcome to Forex Crypto Signal Bot v5!*\n\n"
        "📡 *Data sources:*\n"
        "• 🪙 Crypto → CoinGecko\n"
        "• 💱 Forex  → ExchangeRate-API\n"
        "• 📊 Stocks/Indices/Commodities → Twelve Data\n\n"
        "📋 *Commands:*\n"
        "`/status`          – API health\n"
        "`/signal BTCUSDT`  – Manual signal check\n"
        "`/pairs`           – All monitored pairs\n"
        "`/scan`            – Force scan\n"
        "`/autosignal`      – Toggle auto signals\n"
        "`/stats`           – Statistics\n"
        "`/debug`           – Live API connectivity test\n"
        "`/history`         – RSI history progress per category\n"
        "`/time`            – Nigeria time\n"
        "`/confidence 60`   – Min signal confidence\n"
        "`/duration 5`      – Trade duration (minutes)\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    check_api_health()
    msg = sg.format_status_message(
        auto_signals_on, signal_count,
        coingecko_ok, er_api_ok, td_ok,
        min_confidence, trade_duration,
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_debug(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔬 Running live API tests …")
    lines = ["🔬 *API Debug Report*\n"]

    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        lines.append("✅ *CoinGecko* — reachable" if r.status_code == 200
                     else f"❌ *CoinGecko* — HTTP {r.status_code}")
    except Exception as e:
        lines.append(f"❌ *CoinGecko* — `{e}`")

    try:
        r  = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        d  = r.json()
        ngn = d.get("rates", {}).get("NGN", "N/A")
        lines.append(f"✅ *ExchangeRate-API* — reachable  _(USD/NGN = {ngn})_"
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
            if "price" in d:
                lines.append(f"✅ *Twelve Data* — reachable  _(AAPL = ${d['price']})_")
            else:
                lines.append(f"❌ *Twelve Data* — `{d.get('message', d)}`")
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
    """/history — show how many real price points each category has built up."""
    lines = ["📈 *RSI History Progress*\n",
             f"_Need {config.MIN_PRICE_HISTORY} points per pair for RSI_\n"]
    icons = {"crypto": "🪙", "forex": "💱", "indices": "📈",
             "commodities": "⚗️", "stocks": "🏢"}
    for cat, pairs in config.get_all_pairs().items():
        ready = sum(1 for s in pairs if sg.history_length(s) >= config.MIN_PRICE_HISTORY)
        lines.append(f"{icons[cat]} *{cat.capitalize()}*: {ready}/{len(pairs)} pairs ready")
    lines.append(f"\n_Scans run every {config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX} min._")
    lines.append(f"_Full RSI coverage after ~{config.MIN_PRICE_HISTORY} scans (~{config.MIN_PRICE_HISTORY * config.SCAN_INTERVAL_MIN} min)._")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Manual signal check — shows real RSI, no fake seeding."""
    global signal_count
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: `/signal BTCUSDT`", parse_mode="Markdown"
        )
        return

    symbol = args[0].upper()
    category, sym_key, pair_info = config.find_pair(symbol)
    if category is None:
        await update.message.reply_text(
            f"❌ Unknown pair: `{symbol}`\nUse /pairs to see all.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"🔍 Fetching live price for `{symbol}` …", parse_mode="Markdown"
    )

    price, source = fetch_price(category, sym_key)
    if price is None:
        await update.message.reply_text(
            f"❌ Could not fetch `{symbol}`. Use /debug to check APIs.",
            parse_mode="Markdown",
        )
        return

    # Record the real price (no fake nudges)
    sg.record_price(sym_key, price)
    hist = sg.history_length(sym_key)
    rsi  = sg.calculate_rsi(sg.get_price_history(sym_key))

    if hist < config.MIN_PRICE_HISTORY:
        await update.message.reply_text(
            f"📊 *{symbol}*\n"
            f"Price: `{price}` | History: `{hist}/{config.MIN_PRICE_HISTORY}` points\n\n"
            f"_RSI needs {config.MIN_PRICE_HISTORY} real price points._\n"
            f"_Run /scan a few times or wait for auto scans to build history._",
            parse_mode="Markdown",
        )
        return

    rsi_str = f"`{rsi:.2f}`" if rsi else "_N/A_"

    # Check if RSI is in signal territory
    signal = sg.evaluate_signal(sym_key, price, 0, force=True)
    if signal is None:
        await update.message.reply_text(
            f"📊 *{symbol}*\n"
            f"Price: `{price}` | RSI: {rsi_str}\n\n"
            f"_RSI is in the neutral zone ({config.RSI_OVERSOLD}–{config.RSI_OVERBOUGHT})._\n"
            f"_No BUY or SELL signal right now._",
            parse_mode="Markdown",
        )
        return

    msg = sg.format_signal_message(signal, category, pair_info, source, trade_duration)
    await update.message.reply_text(msg, parse_mode="Markdown")
    last_signal_time[sym_key] = time.time()
    signal_count += 1


async def cmd_pairs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    icons = {"crypto": "🪙", "forex": "💱", "indices": "📈",
             "commodities": "⚗️", "stocks": "🏢"}
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
        "🔄 Running scan … prices are recorded into history.\n"
        "_Signals only fire when RSI crosses threshold based on real history._",
        parse_mode="Markdown",
    )
    count = await run_full_scan(ctx.application.bot, force=False)
    if count == 0:
        await update.message.reply_text(
            "✅ Scan complete — no signals fired.\n\n"
            "_Either RSI is in neutral zone, or history is still building._\n"
            "_Use /history to check progress._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"✅ Scan complete. `{count}` signal(s) sent.", parse_mode="Markdown"
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
        f"📨 Signals sent:      `{signal_count}`\n"
        f"🔍 Pairs monitored:   `{total}`\n"
        f"📈 Pairs with RSI:    `{ready}/{total}`\n"
        f"🎯 Min confidence:    `{min_confidence}%`\n"
        f"⏳ Trade duration:    `{trade_duration} min`\n"
        f"🔄 Auto signals:      {'✅ ON' if auto_signals_on else '❌ OFF'}\n"
        f"📉 RSI thresholds:    Buy<`{config.RSI_OVERSOLD}` | Sell>`{config.RSI_OVERBOUGHT}`\n"
        f"🚦 Max signals/scan:  `{MAX_SIGNALS_PER_SCAN}`\n"
        f"🕐 Updated:           `{now} WAT`\n"
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
    print("  Forex Crypto Signal Bot v5")
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

    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(CommandHandler("signal",     cmd_signal))
    app.add_handler(CommandHandler("pairs",      cmd_pairs))
    app.add_handler(CommandHandler("scan",       cmd_scan))
    app.add_handler(CommandHandler("autosignal", cmd_autosignal))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("debug",      cmd_debug))
    app.add_handler(CommandHandler("history",    cmd_history))
    app.add_handler(CommandHandler("time",       cmd_time))
    app.add_handler(CommandHandler("confidence", cmd_confidence))
    app.add_handler(CommandHandler("duration",   cmd_duration))

    print("[Main] Bot polling …")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
