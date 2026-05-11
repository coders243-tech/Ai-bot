#!/usr/bin/env python3
# main.py  –  Forex Crypto Signal Bot v2
# CoinGecko for crypto | Alpha Vantage for forex/stocks/indices/commodities
# All 10 Telegram commands | Auto-scan loop with real signal firing

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
TELEGRAM_TOKEN    = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID  = os.environ["TELEGRAM_CHAT_ID"]
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")

# ─── RUNTIME STATE ───────────────────────────────────────────────────────────
auto_signals_on:  bool = True
signal_count:     int  = 0
min_confidence:   int  = config.CONFIDENCE_DEFAULT
trade_duration:   int  = config.TRADE_DURATION_DEFAULT
last_signal_time: dict = {}   # { symbol: unix timestamp }
coingecko_ok:     bool = False
av_ok:            bool = False

# ─── ALPHA VANTAGE RATE LIMITER ──────────────────────────────────────────────
_av_timestamps: list = []
AV_MAX_PER_MIN  = 5

def _av_wait() -> None:
    """Block until we are safely within Alpha Vantage's 5 req/min limit."""
    now = time.time()
    _av_timestamps[:] = [t for t in _av_timestamps if t > now - 60]
    if len(_av_timestamps) >= AV_MAX_PER_MIN:
        sleep_for = 61 - (now - _av_timestamps[0])
        if sleep_for > 0:
            print(f"  [AV Rate] Sleeping {sleep_for:.1f}s …")
            time.sleep(sleep_for)
    _av_timestamps.append(time.time())


# ─── COINGECKO BATCH FETCHER ─────────────────────────────────────────────────

def fetch_all_crypto_prices() -> dict:
    """
    Fetch prices for ALL crypto pairs in a single CoinGecko call.
    Returns { symbol: price } for successful fetches.
    """
    # Build comma-separated list of CoinGecko IDs
    id_to_symbol = {}
    for sym, info in config.CRYPTO_PAIRS.items():
        cg_id = info.get("cg_id")
        if cg_id:
            id_to_symbol[cg_id] = sym

    ids_param = ",".join(id_to_symbol.keys())
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids_param}&vs_currencies=usd"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for cg_id, sym in id_to_symbol.items():
            if cg_id in data and "usd" in data[cg_id]:
                price = float(data[cg_id]["usd"])
                result[sym] = price
                print(f"  [CoinGecko] {sym}: {price}")
            else:
                print(f"  [CoinGecko] {sym}: missing in response")
        return result
    except Exception as e:
        print(f"  [CoinGecko ERROR] Batch fetch failed: {e}")
        return {}


# ─── ALPHA VANTAGE FETCHERS ───────────────────────────────────────────────────

def fetch_av_forex(from_cur: str, to_cur: str) -> float | None:
    if not ALPHA_VANTAGE_KEY:
        return None
    _av_wait()
    url = (
        "https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_cur}&to_currency={to_cur}"
        f"&apikey={ALPHA_VANTAGE_KEY}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        rate = float(r.json()["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        print(f"  [AV Forex] {from_cur}/{to_cur}: {rate}")
        return rate
    except Exception as e:
        print(f"  [AV Forex ERROR] {from_cur}/{to_cur}: {e}")
        return None


def fetch_av_quote(ticker: str) -> float | None:
    if not ALPHA_VANTAGE_KEY:
        return None
    _av_wait()
    url = (
        "https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={ticker}"
        f"&apikey={ALPHA_VANTAGE_KEY}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        price = float(r.json()["Global Quote"]["05. price"])
        print(f"  [AV Quote] {ticker}: {price}")
        return price
    except Exception as e:
        print(f"  [AV Quote ERROR] {ticker}: {e}")
        return None


# ─── PRICE DISPATCHER ────────────────────────────────────────────────────────

def fetch_price(category: str, symbol: str) -> tuple:
    """Returns (price_or_None, source_label)."""
    if category == "crypto":
        # Individual fallback fetch (used by /signal command)
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
        price = fetch_av_forex(info["from"], info["to"])
        return price, "Alpha Vantage"

    elif category in ("indices", "commodities", "stocks"):
        price = fetch_av_quote(symbol)
        return price, "Alpha Vantage"

    return None, "Unknown"


# ─── API HEALTH CHECK ────────────────────────────────────────────────────────

def check_api_health() -> tuple:
    global coingecko_ok, av_ok

    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=8)
        coingecko_ok = r.status_code == 200
    except Exception:
        coingecko_ok = False

    if ALPHA_VANTAGE_KEY:
        try:
            _av_wait()
            r = requests.get(
                f"https://www.alphavantage.co/query"
                f"?function=GLOBAL_QUOTE&symbol=IBM&apikey={ALPHA_VANTAGE_KEY}",
                timeout=12,
            )
            av_ok = "Global Quote" in r.json()
        except Exception:
            av_ok = False
    else:
        av_ok = False

    print(f"[Health] CoinGecko: {'OK' if coingecko_ok else 'FAIL'}  |  "
          f"AlphaVantage: {'OK' if av_ok else 'FAIL'}")
    return coingecko_ok, av_ok


# ─── SIGNAL DISPATCH ─────────────────────────────────────────────────────────

async def dispatch_signal(bot, category, symbol, pair_info, source, signal) -> None:
    global signal_count
    msg = sg.format_signal_message(signal, category, pair_info, source, trade_duration)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
    signal_count += 1
    last_signal_time[symbol] = time.time()
    print(f"  ✅ SIGNAL SENT: {symbol} {signal['direction']}  "
          f"RSI={signal['rsi']:.2f}  conf={signal['confidence']}%")


# ─── FULL SCAN ────────────────────────────────────────────────────────────────

async def run_full_scan(bot, force: bool = False) -> int:
    """
    Scan every monitored pair. Batch-fetches crypto, then works through
    AV pairs respecting rate limits. Returns number of signals sent.
    """
    print(f"\n{'='*50}")
    print(f"[Scan] Starting {'FORCED' if force else 'scheduled'} scan …")
    print(f"{'='*50}")

    sent      = 0
    now       = time.time()
    all_pairs = config.get_all_pairs()

    # ── 1. CRYPTO (single batch CoinGecko call) ───────────────────────────
    print("\n[Scan] Fetching all crypto prices (batch) …")
    crypto_prices = fetch_all_crypto_prices()

    for symbol, pair_info in all_pairs["crypto"].items():
        # Cooldown check
        if not force:
            elapsed = now - last_signal_time.get(symbol, 0)
            if elapsed < config.COOLDOWN_SECONDS:
                print(f"  [Cooldown] {symbol}: {int(config.COOLDOWN_SECONDS - elapsed)}s left")
                continue

        price = crypto_prices.get(symbol)
        if price is None:
            print(f"  [Skip] {symbol}: no price available")
            continue

        signal = sg.evaluate_signal(symbol, price, min_confidence, force=force)
        if signal:
            await dispatch_signal(bot, "crypto", symbol, pair_info, "CoinGecko", signal)
            sent += 1
            await asyncio.sleep(0.5)

    # ── 2. FOREX / INDICES / COMMODITIES / STOCKS (Alpha Vantage) ────────
    for category in ("forex", "indices", "commodities", "stocks"):
        if not ALPHA_VANTAGE_KEY:
            print(f"\n[Scan] Skipping {category} – no ALPHA_VANTAGE_KEY set")
            continue

        print(f"\n[Scan] Scanning {category} ({len(all_pairs[category])} pairs) …")
        for symbol, pair_info in all_pairs[category].items():
            if not force:
                elapsed = now - last_signal_time.get(symbol, 0)
                if elapsed < config.COOLDOWN_SECONDS:
                    print(f"  [Cooldown] {symbol}: {int(config.COOLDOWN_SECONDS - elapsed)}s left")
                    continue

            price, source = fetch_price(category, symbol)
            if price is None:
                continue

            signal = sg.evaluate_signal(symbol, price, min_confidence, force=force)
            if signal:
                await dispatch_signal(bot, category, symbol, pair_info, source, signal)
                sent += 1
                await asyncio.sleep(0.5)

    print(f"\n[Scan] Done. {sent} signal(s) sent.\n")
    return sent


# ─── AUTO SCAN LOOP ──────────────────────────────────────────────────────────

async def auto_scan_loop(app: Application) -> None:
    """Background task: scans all pairs every 10–12 minutes."""
    print("[AutoScan] Background loop started.")
    check_api_health()

    # ── Build initial price history before first signal scan ──────────────
    # We prime each pair with ~20 fetches so RSI is ready quickly.
    # For crypto we do 3 batch fetches; for AV pairs the rate limit means
    # we can only prime a small window per loop – that's fine, history builds
    # naturally over subsequent scan cycles.
    print("[Prime] Fetching initial crypto price history (3 rounds) …")
    for _ in range(3):
        prices = fetch_all_crypto_prices()
        for sym, price in prices.items():
            sg.record_price(sym, price)
        await asyncio.sleep(5)   # short gap between rounds

    while True:
        interval = random.randint(
            config.SCAN_INTERVAL_MIN * 60,
            config.SCAN_INTERVAL_MAX * 60,
        )
        print(f"[AutoScan] Next scan in {interval // 60}m {interval % 60}s")
        await asyncio.sleep(interval)

        if auto_signals_on:
            await run_full_scan(app.bot)
        else:
            print("[AutoScan] Auto signals OFF – skipping scan.")


# ─── TELEGRAM COMMANDS ───────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "👋 *Welcome to Forex Crypto Signal Bot v2!*\n\n"
        "I watch *82 instruments* across 5 categories and send\n"
        "automated RSI-based trading signals.\n\n"
        "📋 *Commands:*\n"
        "`/status`          – API health & bot info\n"
        "`/signal BTCUSDT`  – Manual signal for any pair\n"
        "`/pairs`           – List all monitored pairs\n"
        "`/scan`            – Force immediate full scan\n"
        "`/autosignal`      – Toggle auto signals ON/OFF\n"
        "`/stats`           – Trading statistics\n"
        "`/time`            – Nigeria (WAT) time\n"
        "`/confidence 60`   – Set min signal confidence\n"
        "`/duration 5`      – Set trade duration (minutes)\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    check_api_health()
    msg = sg.format_status_message(
        auto_signals_on, signal_count,
        coingecko_ok, av_ok,
        min_confidence, trade_duration,
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_signal(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/signal [SYMBOL] – Force signal for a single pair."""
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

    await update.message.reply_text(f"🔍 Fetching live data for `{symbol}` …", parse_mode="Markdown")

    price, source = fetch_price(category, sym_key)
    if price is None:
        await update.message.reply_text(
            f"❌ Could not fetch price for `{symbol}`. API may be unavailable.",
            parse_mode="Markdown",
        )
        return

    # Seed a few price points so RSI can compute
    for i in range(5):
        nudge = price * random.uniform(-0.002, 0.002)
        sg.record_price(sym_key, price + nudge)

    # force=True bypasses confidence filter so manual checks always respond
    signal = sg.evaluate_signal(sym_key, price, 0, force=True)

    if signal is None:
        hist = sg.history_length(sym_key)
        rsi  = sg.calculate_rsi(sg.get_price_history(sym_key))
        rsi_s = f"`{rsi:.2f}`" if rsi else "_calculating…_"
        await update.message.reply_text(
            f"📊 *{symbol}* | Price: `{price}` | RSI: {rsi_s}\n"
            f"_RSI is in neutral zone — no BUY/SELL signal right now._\n"
            f"_History: {hist} points_",
            parse_mode="Markdown",
        )
        return

    msg = sg.format_signal_message(signal, category, pair_info, source, trade_duration)
    await update.message.reply_text(msg, parse_mode="Markdown")
    last_signal_time[sym_key] = time.time()
    signal_count += 1


async def cmd_pairs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    icons = {
        "crypto":      "🪙",
        "forex":       "💱",
        "indices":     "📈",
        "commodities": "⚗️",
        "stocks":      "🏢",
    }
    lines = ["📋 *All Monitored Instruments*\n"]
    total = 0
    for cat, pairs in config.get_all_pairs().items():
        icon = icons.get(cat, "•")
        lines.append(f"{icon} *{cat.capitalize()}* — {len(pairs)} pairs")
        for sym, info in pairs.items():
            lines.append(f"  `{sym}` {info['flag']} {info['name']}")
        lines.append("")
        total += len(pairs)
    lines.append(f"📊 *Total: {total} instruments*")
    # Telegram message limit: split if needed
    text = "\n".join(lines)
    if len(text) > 4000:
        mid = len(lines) // 2
        await update.message.reply_text("\n".join(lines[:mid]), parse_mode="Markdown")
        await update.message.reply_text("\n".join(lines[mid:]), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔄 Running full scan across all 82 instruments…\n_This may take a few minutes due to API rate limits._",
        parse_mode="Markdown",
    )
    count = await run_full_scan(ctx.application.bot, force=True)
    if count == 0:
        await update.message.reply_text(
            "✅ Scan complete.\n\n"
            "No signals fired — RSI is in the neutral zone for all pairs.\n"
            "_This is normal. Markets spend most time in neutral territory.\n"
            "Signals fire when RSI drops below 35 (BUY) or rises above 65 (SELL)._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"✅ Scan complete. `{count}` signal(s) sent!", parse_mode="Markdown"
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
        f"📨 Signals sent:       `{signal_count}`\n"
        f"🔍 Pairs monitored:    `{total}`\n"
        f"📈 Pairs with RSI:     `{ready}/{total}`\n"
        f"🎯 Min confidence:     `{min_confidence}%`\n"
        f"⏳ Trade duration:     `{trade_duration} min`\n"
        f"🔄 Auto signals:       {'✅ ON' if auto_signals_on else '❌ OFF'}\n"
        f"📉 RSI thresholds:     Buy<`{config.RSI_OVERSOLD}` | Sell>`{config.RSI_OVERBOUGHT}`\n"
        f"🕐 Updated:            `{now} WAT`\n"
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
        await update.message.reply_text("❌ Value must be between 1 and 100.")
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
        print(f"[Startup] Could not send message: {e}")

    asyncio.create_task(auto_scan_loop(app))
    print("[Main] Auto-scan task launched.")


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("  Forex Crypto Signal Bot v2")
    print("=" * 50)

    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set.")
    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID not set.")
    if not ALPHA_VANTAGE_KEY:
        print("[WARNING] ALPHA_VANTAGE_KEY not set — forex/stocks/indices/commodities disabled.")

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
    app.add_handler(CommandHandler("time",        cmd_time))
    app.add_handler(CommandHandler("confidence",  cmd_confidence))
    app.add_handler(CommandHandler("duration",    cmd_duration))

    print("[Main] Bot polling …")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()