# signal_generator.py
# Handles price history storage, RSI calculation, and Telegram signal formatting.

import math
import random
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

# ─── PRICE HISTORY STORE ─────────────────────────────────────────────────────
# { symbol: deque([price, price, ...], maxlen=100) }
_price_history: dict[str, deque] = {}


def record_price(symbol: str, price: float) -> None:
    """Append a new price to the rolling history for a symbol."""
    if symbol not in _price_history:
        _price_history[symbol] = deque(maxlen=100)
    _price_history[symbol].append(price)


def history_length(symbol: str) -> int:
    """Return how many price points we have stored for a symbol."""
    return len(_price_history.get(symbol, []))


def get_price_history(symbol: str) -> list[float]:
    """Return a copy of the stored price list for a symbol."""
    return list(_price_history.get(symbol, []))


# ─── RSI CALCULATION ─────────────────────────────────────────────────────────

def calculate_rsi(prices: list[float], period: int = config.RSI_PERIOD) -> Optional[float]:
    """
    Calculate RSI using Wilder's smoothed moving average method.
    Returns None if there are not enough data points.
    """
    if len(prices) < period + 1:
        return None  # Not enough data yet

    gains = []
    losses = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))

    # Initial average gain/loss over the first `period` changes
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder's smoothing for remaining periods
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0  # No losses → RSI = 100

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


# ─── SIGNAL EVALUATION ───────────────────────────────────────────────────────

def evaluate_signal(symbol: str, current_price: float, min_confidence: int) -> Optional[dict]:
    """
    Record the price, compute RSI, and return a signal dict if RSI
    crosses the oversold/overbought thresholds and confidence is met.
    Returns None if no signal should fire.
    """
    record_price(symbol, current_price)
    prices = get_price_history(symbol)

    if len(prices) < config.MIN_PRICE_HISTORY:
        print(f"[RSI] {symbol}: only {len(prices)}/{config.MIN_PRICE_HISTORY} points – skipping")
        return None

    rsi = calculate_rsi(prices)
    if rsi is None:
        return None

    print(f"[RSI] {symbol}: price={current_price:.6g}  RSI={rsi:.2f}")

    direction = None
    rsi_label = ""
    if rsi <= config.RSI_OVERSOLD:
        direction = "BUY"
        rsi_label = "OVERSOLD"
    elif rsi >= config.RSI_OVERBOUGHT:
        direction = "SELL"
        rsi_label = "OVERBOUGHT"
    else:
        return None  # No signal in neutral zone

    confidence = _compute_confidence(rsi, direction)
    if confidence < min_confidence:
        print(f"[SIGNAL] {symbol}: confidence {confidence}% below threshold {min_confidence}% – skipping")
        return None

    return {
        "symbol":     symbol,
        "direction":  direction,
        "price":      current_price,
        "rsi":        rsi,
        "rsi_label":  rsi_label,
        "confidence": confidence,
    }


def _compute_confidence(rsi: float, direction: str) -> int:
    """
    Map RSI extreme to a confidence percentage:
    - BUY:  RSI 30→50, confidence 55→99
    - SELL: RSI 70→50, confidence 55→99
    Add a small random jitter (±3%) so signals feel organic.
    """
    if direction == "BUY":
        # Further below 30 = higher confidence
        distance = max(0.0, config.RSI_OVERSOLD - rsi)   # 0–30
        confidence = 55 + (distance / config.RSI_OVERSOLD) * 44
    else:
        distance = max(0.0, rsi - config.RSI_OVERBOUGHT)  # 0–30
        confidence = 55 + (distance / (100 - config.RSI_OVERBOUGHT)) * 44

    jitter = random.randint(-3, 3)
    return min(99, max(55, int(confidence) + jitter))


# ─── NIGERIA TIME HELPERS ────────────────────────────────────────────────────

def _nigeria_now() -> datetime:
    """Return current time in WAT (UTC+1)."""
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    return datetime.now(tz=wat)


def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p")


def _fmt_datetime(dt: datetime) -> str:
    return dt.strftime("%d %b %Y  %I:%M %p")


def _countdown(target: datetime) -> str:
    """Return mm:ss countdown string from now to target."""
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    now = datetime.now(tz=wat)
    diff = int((target - now).total_seconds())
    if diff <= 0:
        return "00:00"
    m, s = divmod(diff, 60)
    return f"{m:02d}:{s:02d}"


# ─── SIGNAL MESSAGE FORMATTER ────────────────────────────────────────────────

def format_signal_message(
    signal: dict,
    category: str,
    pair_info: dict,
    source: str,
    trade_duration: int = config.TRADE_DURATION_DEFAULT,
) -> str:
    """
    Build the full Telegram-formatted signal message.

    Parameters
    ----------
    signal       : dict from evaluate_signal()
    category     : "crypto" | "forex" | "indices" | etc.
    pair_info    : entry from config (has 'name', 'flag')
    source       : "Binance" or "Alpha Vantage"
    trade_duration: minutes for the trade
    """
    now_wat = _nigeria_now()
    entry_time = now_wat + timedelta(minutes=3)
    entry_time_str = _fmt_time(entry_time)

    direction = signal["direction"]
    price = signal["price"]
    rsi = signal["rsi"]
    rsi_label = signal["rsi_label"]
    confidence = signal["confidence"]
    flag = pair_info["flag"]
    pair_name = pair_info["name"]
    symbol = signal["symbol"]

    # Direction visuals
    if direction == "BUY":
        dir_emoji = "🟢🐂"
        dir_arrow = "⬆️ BUY"
    else:
        dir_emoji = "🔴🐻"
        dir_arrow = "⬇️ SELL"

    # Price formatting (crypto shows more decimals)
    if category == "crypto":
        price_str = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
    elif category == "forex":
        price_str = f"{price:.5f}"
    else:
        price_str = f"${price:,.2f}"

    # Take profit & stop loss
    tp_pct = config.TP_SL_PCT
    if direction == "BUY":
        tp = price * (1 + tp_pct)
        sl = price * (1 - tp_pct)
    else:
        tp = price * (1 - tp_pct)
        sl = price * (1 + tp_pct)

    if category == "crypto":
        tp_str = f"${tp:,.4f}" if tp < 1 else f"${tp:,.2f}"
        sl_str = f"${sl:,.4f}" if sl < 1 else f"${sl:,.2f}"
    elif category == "forex":
        tp_str, sl_str = f"{tp:.5f}", f"{sl:.5f}"
    else:
        tp_str, sl_str = f"${tp:,.2f}", f"${sl:,.2f}"

    # Martingale levels
    martingale_lines = []
    for level in range(1, config.MARTINGALE_LEVELS + 1):
        m_time = entry_time + timedelta(minutes=config.MARTINGALE_GAP_MIN * level)
        countdown_str = _countdown(m_time)
        multiplier = 2 ** (level - 1)
        martingale_lines.append(
            f"  ├ Level {level} (×{multiplier}) → {_fmt_time(m_time)}  ⏱ {countdown_str}"
        )
    martingale_block = "\n".join(martingale_lines)

    # Confidence bar
    filled = math.ceil(confidence / 10)
    bar = "█" * filled + "░" * (10 - filled)

    # Entry countdown
    entry_countdown = _countdown(entry_time)

    # Category label
    cat_label = category.capitalize()

    message = (
        f"{'─' * 30}\n"
        f"{flag}  *{pair_name}*  ({symbol})\n"
        f"{'─' * 30}\n"
        f"{dir_emoji}  *{dir_arrow}*\n\n"
        f"💰 *Price:*  `{price_str}`\n"
        f"⏰ *Entry Time:*  `{entry_time_str}` WAT  ⏱ `{entry_countdown}`\n\n"
        f"📊 *RSI ({config.RSI_PERIOD}):*  `{rsi:.2f}`  →  _{rsi_label}_\n\n"
        f"🎯 *Confidence:*  `{confidence}%`\n"
        f"`[{bar}]`\n\n"
        f"📈 *Martingale Ladder:*\n"
        f"{martingale_block}\n\n"
        f"✅ *Take Profit:*  `{tp_str}`  (+{tp_pct*100:.1f}%)\n"
        f"🛑 *Stop Loss:*    `{sl_str}`  (-{tp_pct*100:.1f}%)\n\n"
        f"⏳ *Trade Duration:*  `{trade_duration} min`\n"
        f"📡 *Source:*  _{source}_\n"
        f"🏷 *Category:*  _{cat_label}_\n"
        f"🕐 *Signal Time:*  `{_fmt_datetime(now_wat)} WAT`\n"
        f"{'─' * 30}"
    )

    return message


# ─── STARTUP / STATUS HELPERS ────────────────────────────────────────────────

def format_startup_message(chat_id: str) -> str:
    now = _fmt_datetime(_nigeria_now())
    all_pairs = config.get_all_pairs()
    total = sum(len(v) for v in all_pairs.values())
    return (
        "🚀 *Forex Crypto Signal Bot is LIVE!*\n\n"
        f"📅 Started:  `{now} WAT`\n"
        f"📊 Monitoring `{total}` instruments across 5 categories\n"
        f"🔁 Auto scan every `{config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX}` min\n"
        f"📉 RSI Period:  `{config.RSI_PERIOD}`  |  "
        f"Buy <`{config.RSI_OVERSOLD}`  |  Sell >`{config.RSI_OVERBOUGHT}`\n\n"
        "Send /help to see all commands.\n"
        "Send /autosignal to toggle auto signals ON/OFF."
    )


def format_status_message(
    auto_on: bool,
    signal_count: int,
    binance_ok: bool,
    av_ok: bool,
    min_confidence: int,
    trade_duration: int,
) -> str:
    now = _fmt_datetime(_nigeria_now())
    auto_str = "✅ ON" if auto_on else "❌ OFF"
    b_str = "✅ Connected" if binance_ok else "❌ Unreachable"
    av_str = "✅ Connected" if av_ok else "❌ Unreachable"
    return (
        "🤖 *Bot Status*\n"
        f"{'─' * 28}\n"
        f"🕐 Time:           `{now} WAT`\n"
        f"📡 Binance API:    {b_str}\n"
        f"📡 Alpha Vantage:  {av_str}\n"
        f"🔄 Auto Signals:   {auto_str}\n"
        f"📨 Signals Sent:   `{signal_count}`\n"
        f"🎯 Min Confidence: `{min_confidence}%`\n"
        f"⏳ Trade Duration: `{trade_duration} min`\n"
    )