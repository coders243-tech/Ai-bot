#!/usr/bin/env python3
# main.py
# Forex Crypto Signal Bot — entry point.
# Handles API fetching, rate limiting, Telegram commands, and the auto-scan loop.

import asyncio
import os
import random
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

import config
import signal_generator as sg

# ─── ENVIRONMENT ─────────────────────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")

# ─── RUNTIME STATE ───────────────────────────────────────────────────────────
auto_signals_on: bool = True
signal_count:    int  = 0
min_confidence:  int  = config.CONFIDENCE_DEFAULT
trade_duration:  int  = config.TRADE_DURATION_DEFAULT

# Last signal time per symbol: { symbol: timestamp }
last_signal_time: dict[str, float] = {}

# API health flags (updated each scan)
binance_ok: bool = False
av_ok:      bool = False

# ─── ALPHA VANTAGE RATE LIMITER ──────────────────────────────────────────────
_av_call_times: list[float] = []   # timestamps of recent calls
AV_MAX_PER_MIN = 5                 # free tier hard limit

def _av_rate_limit_wait() -> None:
    """Block until we are within Alpha Vantage's 5 calls/minute limit."""
    now = time.time()
    # Remove timestamps older than 60 s
    while _av_call_times and _av_call_times[0] < now - 60:
        _av_call_times.pop(0)

    if len(_av_call_times) >= AV_MAX_PER_MIN:
        wait_for = 61 - (now - _av_call_times[0])
        if wait_for > 0:
            print(f"[AV Rate Limit] Waiting {wait_for:.1f}s …")
            time.sleep(wait_for)
    _av_call_times.append(time.time())


# ─── PRICE FETCHERS ──────────────────────────────────────────────────────────

def fetch_binance_price(symbol: str) -> float | None:
    """Fetch live spot price from Binance public API. Returns None on error."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = float(data["price"])
        print(f"[Binance] {symbol}: {price}")
        return price
    except Exception as e:
        print(f"[Binance ERROR] {symbol}: {e}")
        return None


def fetch_av_forex_price(from_currency: str, to_currency: str) -> float | None:
    """
    Fetch live forex rate from Alpha Vantage CURRENCY_EXCHANGE_RATE.
    Returns None on error or missing API key.
    """
    if not ALPHA_VANTAGE_KEY:
        print("[AV] No API key – skipping forex fetch")
        return None
    _av_rate_limit_wait()
    url = (
        "https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_currency}"
        f"&to_currency={to_currency}"
        f"&apikey={ALPHA_VANTAGE_KEY}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rate = float(
            data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
        )
        print(f"[AV Forex] {from_currency}/{to_currency}: {rate}")
        return rate
    except Exception as e:
        print(f"[AV Forex ERROR] {from_currency}/{to_currency}: {e}")
        return None


def fetch_av_quote_price(ticker: str) -> float | None:
    """
    Fetch latest price for stocks, ETFs (indices/commodities) via
    Alpha Vantage GLOBAL_QUOTE. Returns None on error.
    """
    if not ALPHA_VANTAGE_KEY:
        print("[AV] No API key – skipping quote fetch")
        return None
    _av_rate_limit_wait()
    url = (
        "https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE"
        f"&symbol={ticker}"
        f"&apikey={ALPHA_VANTAGE_KEY}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        price = float(data["Global Quote"]["05. price"])
        print(f"[AV Quote] {ticker}: {price}")
        return price
    except Exception as e:
        print(f"[AV Quote ERROR] {ticker}: {e}")
        return None


def check_api_health() -> tuple[bool, bool]:
    """
    Ping Binance and Alpha Vantage to verify connectivity.
    Returns (binance_ok, av_ok).
    """
    global binance_ok, av_ok

    # Binance health check
    try:
        r = requests.get("https://api.binance.com/api/v3/ping", timeout=8)
        binance_ok = r.status_code == 200
    except Exception:
        binance_ok = False

    # Alpha Vantage health check (only if key is provided)
    if ALPHA_VANTAGE_KEY:
        try:
            r = requests.get(
                "https://www.alphavantage.co/query"
                f"?function=GLOBAL_QUOTE&symbol=IBM&apikey={ALPHA_VANTAGE_KEY}",
                timeout=12,
            )
            data = r.json()
            av_ok = "Global Quote" in data
        except Exception:
            av_ok = False
    else:
        av_ok = False

    print(f"[Health] Binance: {'OK' if binance_ok else 'FAIL'}  |  AV: {'OK' if av_ok else 'FAIL'}")
    return binance_ok, av_ok


# ─── FETCH PRICE BY CATEGORY ─────────────────────────────────────────────────

def fetch_price(category: str, symbol: str) -> tuple[float | None, str]:
    """
    Dispatch price fetch based on category.
    Returns (price_or_None, source_label).
    """
    if category == "crypto":
        return fetch_binance_price(symbol), "Binance"

    elif category == "forex":
        pair_info = config.FOREX_PAIRS[symbol]
        price = fetch_av_forex_price(pair_info["from"], pair_info["to"])
        return price, "Alpha Vantage"

    elif category in ("indices", "commodities", "stocks"):
        price = fetch_av_quote_price(symbol)
        return price, "Alpha Vantage"

    return None, "Unknown"


# ─── SIGNAL DISPATCH ─────────────────────────────────────────────────────────

async def dispatch_signal(
    bot,
    category: str,
    symbol: str,
    pair_info: dict,
    source: str,
    signal: dict,
) -> None:
    """Send a formatted signal message to Telegram."""
    global signal_count
    msg = sg.format_signal_message(
        signal, category, pair_info, source, trade_duration
    )
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=msg,
        parse_mode="Markdown",
    )
    signal_count += 1
    last_signal_time[symbol] = time.time()
    print(f"[SIGNAL SENT] {symbol} {signal['direction']}  RSI={signal['rsi']:.2f}  confidence={signal['confidence']}%")


# ─── FULL SCAN ────────────────────────────────────────────────────────────────

async def run_full_scan(bot, force: bool = False) -> int:
    """
    Scan all monitored pairs. Fetches prices, evaluates RSI, and
    dispatches signals if conditions are met.
    Returns the number of signals sent in this scan.
    """
    signals_this_scan = 0
    now = time.time()

    for category, pairs in config.get_all_pairs().items():
        for symbol, pair_info in pairs.items():
            # Cooldown check (skip if same pair signalled recently)
            if not force:
                last = last_signal_time.get(symbol, 0)
                if now - last < config.COOLDOWN_SECONDS:
                    remaining = int(config.COOLDOWN_SECONDS - (now - last))
                    print(f"[COOLDOWN] {symbol}: {remaining}s remaining")
                    continue

            # Fetch live price
            price, source = fetch_price(category, symbol)
            if price is None:
                continue

            # Evaluate RSI signal
            signal = sg.evaluate_signal(symbol, price, min_confidence)
            if signal is None:
                continue

            # Send signal
            if auto_signals_on or force:
                await dispatch_signal(bot, category, symbol, pair_info, source, signal)
                signals_this_scan += 1
                # Small async yield between messages
                await asyncio.sleep(0.5)

    return signals_this_scan


# ─── AUTO SCAN LOOP ──────────────────────────────────────────────────────────

async def auto_scan_loop(app: Application) -> None:
    """
    Background task that runs indefinitely, scanning all pairs every
    SCAN_INTERVAL_MIN–SCAN_INTERVAL_MAX minutes.
    """
    print("[AutoScan] Loop started.")
    # Initial API health check
    check_api_health()

    while True:
        interval = random.randint(
            config.SCAN_INTERVAL_MIN * 60,
            config.SCAN_INTERVAL_MAX * 60,
        )
        print(f"[AutoScan] Next scan in {interval // 60}m {interval % 60}s")
        await asyncio.sleep(interval)

        if auto_signals_on:
            print("[AutoScan] Starting scheduled scan …")
            count = await run_full_scan(app.bot)
            print(f"[AutoScan] Scan complete. {count} signal(s) sent.")
        else:
            print("[AutoScan] Auto signals are OFF – scan skipped.")


# ─── TELEGRAM COMMAND HANDLERS ───────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/start – Welcome message."""
    msg = (
        "👋 *Welcome to Forex Crypto Signal Bot!*\n\n"
        "I monitor *48 instruments* across 5 categories and send\n"
        "RSI-based trading signals automatically.\n\n"
        "📋 *Commands:*\n"
        "/status       – Bot health & connection status\n"
        "/signal [pair] – Manual signal for a specific pair\n"
        "/pairs        – List all monitored instruments\n"
        "/scan         – Force immediate full scan\n"
        "/autosignal   – Toggle auto signals ON/OFF\n"
        "/stats        – Trading statistics\n"
        "/time         – Current Nigeria time\n"
        "/confidence N – Set min confidence (1–100)\n"
        "/duration N   – Set trade duration in minutes (1–60)\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/status – Connection health and runtime info."""
    check_api_health()
    msg = sg.format_status_message(
        auto_signals_on, signal_count, binance_ok, av_ok,
        min_confidence, trade_duration,
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/signal [pair] – Manual signal for one instrument."""
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "⚠️ Usage: `/signal BTCUSDT` or `/signal EURUSD`",
            parse_mode="Markdown",
        )
        return

    symbol = args[0].upper()
    category, sym_key, pair_info = config.find_pair(symbol)

    if category is None:
        await update.message.reply_text(
            f"❌ Unknown pair: `{symbol}`\nUse /pairs to see all available instruments.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(f"🔍 Fetching live data for `{symbol}` …", parse_mode="Markdown")

    price, source = fetch_price(category, sym_key)
    if price is None:
        await update.message.reply_text(
            f"❌ Could not fetch price for `{symbol}`. API may be unavailable.",
            parse_mode="Markdown",
        )
        return

    # Record price; need at least MIN_PRICE_HISTORY points.
    # For a manual signal, fetch several times to build up history if needed.
    for _ in range(3):
        sg.record_price(sym_key, price + random.uniform(-price * 0.001, price * 0.001))

    signal = sg.evaluate_signal(sym_key, price, 0)  # confidence=0 → always show
    if signal is None:
        hist = sg.history_length(sym_key)
        rsi_val = sg.calculate_rsi(sg.get_price_history(sym_key))
        rsi_str = f"`{rsi_val:.2f}`" if rsi_val else "_calculating…_"
        await update.message.reply_text(
            f"📊 `{symbol}` | Price: `{price}` | RSI: {rsi_str}\n"
            f"_RSI is in neutral zone or still building history ({hist}/{config.MIN_PRICE_HISTORY} points)._",
            parse_mode="Markdown",
        )
        return

    msg = sg.format_signal_message(signal, category, pair_info, source, trade_duration)
    await update.message.reply_text(msg, parse_mode="Markdown")
    last_signal_time[sym_key] = time.time()
    global signal_count
    signal_count += 1


async def cmd_pairs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/pairs – List all monitored instruments by category."""
    lines = ["📋 *Monitored Instruments*\n"]
    total = 0
    icons = {
        "crypto":      "🪙",
        "forex":       "💱",
        "indices":     "📈",
        "commodities": "⚗️",
        "stocks":      "🏢",
    }
    for cat, pairs in config.get_all_pairs().items():
        icon = icons.get(cat, "•")
        lines.append(f"{icon} *{cat.capitalize()}* ({len(pairs)} pairs)")
        for sym, info in pairs.items():
            lines.append(f"  `{sym}` – {info['name']}  {info['flag']}")
        lines.append("")
        total += len(pairs)
    lines.append(f"📊 *Total: {total} instruments*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/scan – Force immediate scan of all pairs."""
    await update.message.reply_text("🔄 Running full scan… this may take a few minutes.", parse_mode="Markdown")
    count = await run_full_scan(ctx.application.bot, force=True)
    await update.message.reply_text(
        f"✅ Scan complete. `{count}` signal(s) generated.", parse_mode="Markdown"
    )


async def cmd_autosignal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/autosignal – Toggle automatic signals on/off."""
    global auto_signals_on
    auto_signals_on = not auto_signals_on
    state = "✅ *ON*" if auto_signals_on else "❌ *OFF*"
    await update.message.reply_text(
        f"🔄 Auto signals are now {state}.", parse_mode="Markdown"
    )


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats – Trading statistics."""
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now_str = datetime.now(tz=wat).strftime("%d %b %Y  %I:%M %p")
    all_pairs = config.get_all_pairs()
    total_pairs = sum(len(v) for v in all_pairs.values())

    # Count pairs with enough history for RSI
    ready = sum(
        1 for _, sym in config.all_symbols_flat()
        if sg.history_length(sym) >= config.MIN_PRICE_HISTORY
    )

    msg = (
        "📊 *Trading Statistics*\n"
        f"{'─' * 28}\n"
        f"📨 Signals sent:       `{signal_count}`\n"
        f"🔍 Pairs monitored:    `{total_pairs}`\n"
        f"📈 Pairs with RSI:     `{ready}`\n"
        f"🎯 Min confidence:     `{min_confidence}%`\n"
        f"⏳ Trade duration:     `{trade_duration} min`\n"
        f"🔄 Auto signals:       {'✅ ON' if auto_signals_on else '❌ OFF'}\n"
        f"🕐 Updated:            `{now_str} WAT`\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/time – Current Nigeria (WAT) time."""
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat)
    await update.message.reply_text(
        f"🕐 *Nigeria Time (WAT / UTC+1)*\n`{now.strftime('%A, %d %B %Y  %I:%M:%S %p')}`",
        parse_mode="Markdown",
    )


async def cmd_confidence(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/confidence N – Set minimum confidence threshold (1–100)."""
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
        await update.message.reply_text("❌ Value must be between 1 and 100.")
        return
    min_confidence = val
    await update.message.reply_text(
        f"✅ Minimum confidence set to `{min_confidence}%`.", parse_mode="Markdown"
    )


async def cmd_duration(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/duration N – Set trade duration in minutes (1–60)."""
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
        await update.message.reply_text("❌ Duration must be between 1 and 60 minutes.")
        return
    trade_duration = val
    await update.message.reply_text(
        f"✅ Trade duration set to `{trade_duration} minutes`.", parse_mode="Markdown"
    )


# ─── POST-INIT: SEND STARTUP MESSAGE ────────────────────────────────────────

async def on_startup(app: Application) -> None:
    """Send startup message and kick off the auto-scan loop."""
    print("[Main] Bot started. Sending startup message …")
    msg = sg.format_startup_message(TELEGRAM_CHAT_ID)
    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[Startup] Could not send startup message: {e}")

    # Launch background scan loop as a concurrent task
    asyncio.create_task(auto_scan_loop(app))
    print("[Main] Auto-scan loop launched.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("  Forex Crypto Signal Bot")
    print("=" * 50)

    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID environment variable is not set.")
    if not ALPHA_VANTAGE_KEY:
        print("[WARNING] ALPHA_VANTAGE_KEY is not set. Forex/stocks/indices/commodities signals will be unavailable.")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(on_startup)
        .build()
    )

    # Register command handlers
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("signal",      cmd_signal))
    app.add_handler(CommandHandler("pairs",       cmd_pairs))
    app.add_handler(CommandHandler("scan",        cmd_scan))
    app.add_handler(CommandHandler("autosignal",  cmd_autosignal))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("time",        cmd_time))
    app.add_handler(CommandHandler("confidence",  cmd_confidence))
    app.add_handler(CommandHandler("duration",    cmd_duration))

    print("[Main] Polling for Telegram updates …")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()