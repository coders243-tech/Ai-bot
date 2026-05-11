# signal_generator.py
# Price history, RSI calculation, signal evaluation, and message formatting.

import math
import random
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

# ─── PRICE HISTORY ───────────────────────────────────────────────────────────
# Rolling price store: { symbol: deque of floats }
_price_history: dict[str, deque] = {}


def record_price(symbol: str, price: float) -> None:
    """Append a live price to the rolling history for a symbol."""
    if symbol not in _price_history:
        _price_history[symbol] = deque(maxlen=100)
    _price_history[symbol].append(price)


def history_length(symbol: str) -> int:
    return len(_price_history.get(symbol, []))


def get_price_history(symbol: str) -> list:
    return list(_price_history.get(symbol, []))


def clear_history(symbol: str) -> None:
    if symbol in _price_history:
        _price_history[symbol].clear()


# ─── RSI CALCULATION (Wilder's Smoothed MA) ──────────────────────────────────

def calculate_rsi(prices: list, period: int = config.RSI_PERIOD) -> Optional[float]:
    """
    Compute RSI using Wilder's Smoothed Moving Average.
    Returns None when there are fewer than (period + 1) prices.
    """
    if len(prices) < period + 1:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains  = [max(d, 0.0) for d in deltas]
    losses = [abs(min(d, 0.0)) for d in deltas]

    # Seed averages from first `period` changes
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder smoothing over remaining changes
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs  = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


# ─── CONFIDENCE SCORING ──────────────────────────────────────────────────────

def _compute_confidence(rsi: float, direction: str) -> int:
    """
    Map how extreme the RSI is to a confidence percentage (55 – 98).
    Further from neutral = higher confidence.
    """
    if direction == "BUY":
        # RSI oversold threshold is 35; lower = more extreme
        distance = max(0.0, config.RSI_OVERSOLD - rsi)
        max_dist = config.RSI_OVERSOLD  # 0–35
        confidence = 55 + (distance / max(max_dist, 1)) * 43
    else:
        distance = max(0.0, rsi - config.RSI_OVERBOUGHT)
        max_dist = 100 - config.RSI_OVERBOUGHT  # 0–35
        confidence = 55 + (distance / max(max_dist, 1)) * 43

    jitter = random.randint(-2, 3)
    return min(98, max(55, int(confidence) + jitter))


# ─── SIGNAL EVALUATION ───────────────────────────────────────────────────────

def evaluate_signal(
    symbol: str,
    current_price: float,
    min_confidence: int,
    force: bool = False,
) -> Optional[dict]:
    """
    Record the price, compute RSI, and return a signal dict when:
      - RSI crosses oversold/overbought threshold
      - Confidence >= min_confidence  (ignored when force=True)

    Returns None when no signal should fire.
    """
    record_price(symbol, current_price)
    prices = get_price_history(symbol)
    n = len(prices)

    if n < config.MIN_PRICE_HISTORY:
        print(f"  [RSI] {symbol}: {n}/{config.MIN_PRICE_HISTORY} history points – building…")
        return None

    rsi = calculate_rsi(prices)
    if rsi is None:
        print(f"  [RSI] {symbol}: not enough deltas for RSI yet")
        return None

    print(f"  [RSI] {symbol}: price={current_price:.6g}  RSI={rsi:.2f}  "
          f"(buy<{config.RSI_OVERSOLD} / sell>{config.RSI_OVERBOUGHT})")

    direction = None
    rsi_label = ""
    if rsi <= config.RSI_OVERSOLD:
        direction = "BUY"
        rsi_label = "OVERSOLD"
    elif rsi >= config.RSI_OVERBOUGHT:
        direction = "SELL"
        rsi_label = "OVERBOUGHT"
    else:
        return None   # RSI neutral – no signal

    confidence = _compute_confidence(rsi, direction)

    if not force and confidence < min_confidence:
        print(f"  [SIGNAL] {symbol}: confidence {confidence}% < threshold {min_confidence}% – skipped")
        return None

    return {
        "symbol":     symbol,
        "direction":  direction,
        "price":      current_price,
        "rsi":        rsi,
        "rsi_label":  rsi_label,
        "confidence": confidence,
    }


# ─── NIGERIA TIME ─────────────────────────────────────────────────────────────

def _nigeria_now() -> datetime:
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    return datetime.now(tz=wat)

def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p")

def _fmt_datetime(dt: datetime) -> str:
    return dt.strftime("%d %b %Y  %I:%M %p")

def _countdown(target: datetime) -> str:
    wat = timezone(timedelta(hours=config.TIMEZONE_OFFSET))
    diff = int((target - datetime.now(tz=wat)).total_seconds())
    if diff <= 0:
        return "00:00"
    m, s = divmod(diff, 60)
    return f"{m:02d}:{s:02d}"


# ─── SIGNAL MESSAGE FORMATTER ────────────────────────────────────────────────

def format_signal_message(
    signal:         dict,
    category:       str,
    pair_info:      dict,
    source:         str,
    trade_duration: int = config.TRADE_DURATION_DEFAULT,
) -> str:
    now_wat    = _nigeria_now()
    entry_time = now_wat + timedelta(minutes=3)

    direction  = signal["direction"]
    price      = signal["price"]
    rsi        = signal["rsi"]
    rsi_label  = signal["rsi_label"]
    confidence = signal["confidence"]
    flag       = pair_info["flag"]
    pair_name  = pair_info["name"]
    symbol     = signal["symbol"]

    # Visuals
    dir_emoji  = "🟢🐂" if direction == "BUY" else "🔴🐻"
    dir_arrow  = "⬆️ BUY"  if direction == "BUY" else "⬇️ SELL"

    # Price formatting
    if category == "crypto":
        price_str = f"${price:,.6f}" if price < 0.01 else (f"${price:,.4f}" if price < 1 else f"${price:,.2f}")
    elif category == "forex":
        price_str = f"{price:.5f}"
    else:
        price_str = f"${price:,.2f}"

    # TP / SL
    pct = config.TP_SL_PCT
    tp  = price * (1 + pct) if direction == "BUY" else price * (1 - pct)
    sl  = price * (1 - pct) if direction == "BUY" else price * (1 + pct)

    def fmt_p(v):
        if category == "crypto":
            return f"${v:,.6f}" if v < 0.01 else (f"${v:,.4f}" if v < 1 else f"${v:,.2f}")
        elif category == "forex":
            return f"{v:.5f}"
        return f"${v:,.2f}"

    tp_str = fmt_p(tp)
    sl_str = fmt_p(sl)

    # Martingale ladder
    mart_lines = []
    for lvl in range(1, config.MARTINGALE_LEVELS + 1):
        m_time = entry_time + timedelta(minutes=config.MARTINGALE_GAP_MIN * lvl)
        mult   = 2 ** (lvl - 1)
        mart_lines.append(
            f"  ├ Level {lvl} (×{mult}) → `{_fmt_time(m_time)}` WAT  ⏱ `{_countdown(m_time)}`"
        )

    # Confidence bar
    filled = math.ceil(confidence / 10)
    bar    = "█" * filled + "░" * (10 - filled)

    msg = (
        f"{'━' * 32}\n"
        f"{flag}  *{pair_name}*\n"
        f"{'━' * 32}\n"
        f"{dir_emoji}  *{dir_arrow}*\n\n"
        f"💰 *Live Price:*  `{price_str}`\n"
        f"⏰ *Entry Time:*  `{_fmt_time(entry_time)}` WAT  ⏱ `{_countdown(entry_time)}`\n\n"
        f"📊 *RSI‑{config.RSI_PERIOD}:*  `{rsi:.2f}`  →  _{rsi_label}_\n\n"
        f"🎯 *Confidence:*  `{confidence}%`\n"
        f"`[{bar}]`\n\n"
        f"📈 *Martingale Ladder:*\n"
        + "\n".join(mart_lines) +
        f"\n\n✅ *Take Profit:*  `{tp_str}`  _(+{pct*100:.1f}%)_\n"
        f"🛑 *Stop Loss:*    `{sl_str}`  _(-{pct*100:.1f}%)_\n\n"
        f"⏳ *Duration:*  `{trade_duration} min`\n"
        f"📡 *Source:*  _{source}_\n"
        f"🏷 *Category:*  _{category.capitalize()}_\n"
        f"🕐 *Sent:*  `{_fmt_datetime(now_wat)} WAT`\n"
        f"{'━' * 32}"
    )
    return msg


# ─── STARTUP / STATUS MESSAGES ───────────────────────────────────────────────

def format_startup_message() -> str:
    now   = _fmt_datetime(_nigeria_now())
    total = sum(len(v) for v in config.get_all_pairs().values())
    return (
        "🚀 *Forex Crypto Signal Bot v2 is LIVE!*\n\n"
        f"📅 *Started:*  `{now} WAT`\n"
        f"📊 *Monitoring:*  `{total}` instruments across 5 categories\n"
        f"🔁 *Auto scan:*  every `{config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX}` min\n"
        f"📉 *RSI-{config.RSI_PERIOD}:*  Buy < `{config.RSI_OVERSOLD}` | Sell > `{config.RSI_OVERBOUGHT}`\n"
        f"🎯 *Min confidence:*  `{config.CONFIDENCE_DEFAULT}%`\n\n"
        "Use /pairs to see all instruments.\n"
        "Use /scan to trigger an immediate scan.\n"
        "Use /autosignal to toggle signals ON/OFF."
    )


def format_status_message(
    auto_on:        bool,
    signal_count:   int,
    cg_ok:          bool,
    av_ok:          bool,
    min_confidence: int,
    trade_duration: int,
) -> str:
    now     = _fmt_datetime(_nigeria_now())
    auto_s  = "✅ ON"  if auto_on  else "❌ OFF"
    cg_s    = "✅ OK"  if cg_ok    else "❌ Unreachable"
    av_s    = "✅ OK"  if av_ok    else "❌ Unreachable"
    return (
        "🤖 *Bot Status*\n"
        f"{'─' * 30}\n"
        f"🕐 Time:             `{now} WAT`\n"
        f"📡 CoinGecko API:    {cg_s}\n"
        f"📡 Alpha Vantage:    {av_s}\n"
        f"🔄 Auto Signals:     {auto_s}\n"
        f"📨 Signals Sent:     `{signal_count}`\n"
        f"🎯 Min Confidence:   `{min_confidence}%`\n"
        f"⏳ Trade Duration:   `{trade_duration} min`\n"
        f"📊 RSI Thresholds:   Buy < `{config.RSI_OVERSOLD}` | Sell > `{config.RSI_OVERBOUGHT}`\n"
    )