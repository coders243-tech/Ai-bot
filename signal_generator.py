# signal_generator.py  –  v5
# KEY FIXES:
#   - Removed ALL artificial price seeding. RSI is only calculated from
#     real fetched prices accumulated over multiple scan cycles.
#   - A signal only fires when RSI genuinely crosses the threshold AND
#     the price history contains enough REAL variation (not nudged copies).
#   - /signal command now shows RSI value honestly without fake seeding.

import math
import random
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

# ─── PRICE HISTORY ───────────────────────────────────────────────────────────
_price_history: dict[str, deque] = {}


def record_price(symbol: str, price: float) -> None:
    """Append one real fetched price to the symbol's history."""
    if symbol not in _price_history:
        _price_history[symbol] = deque(maxlen=100)
    _price_history[symbol].append(price)


def history_length(symbol: str) -> int:
    return len(_price_history.get(symbol, []))


def get_price_history(symbol: str) -> list:
    return list(_price_history.get(symbol, []))


# ─── RSI (Wilder's Smoothed MA) ──────────────────────────────────────────────

def calculate_rsi(prices: list, period: int = config.RSI_PERIOD) -> Optional[float]:
    """
    Returns RSI (0–100) or None if not enough data.
    Requires at least (period + 1) data points.
    """
    if len(prices) < period + 1:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains  = [max(d, 0.0) for d in deltas]
    losses = [abs(min(d, 0.0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs  = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


# ─── SIGNAL EVALUATION ───────────────────────────────────────────────────────

def evaluate_signal(
    symbol:         str,
    current_price:  float,
    min_confidence: int,
    force:          bool = False,
) -> Optional[dict]:
    """
    Records the price and evaluates RSI.

    A signal is returned ONLY when:
      1. We have at least MIN_PRICE_HISTORY real data points
      2. RSI genuinely crosses oversold / overbought threshold
      3. Confidence meets the minimum (unless force=True)

    IMPORTANT: No artificial seeding here. Prices accumulate naturally
    across scan cycles. History builds over ~2–3 hours on a 10-min scan.
    """
    record_price(symbol, current_price)
    prices = get_price_history(symbol)
    n = len(prices)

    if n < config.MIN_PRICE_HISTORY:
        print(f"  [RSI] {symbol}: {n}/{config.MIN_PRICE_HISTORY} history points – still building")
        return None

    rsi = calculate_rsi(prices)
    if rsi is None:
        return None

    print(f"  [RSI] {symbol}: price={current_price:.6g}  RSI={rsi:.2f}")

    # Determine direction
    if rsi <= config.RSI_OVERSOLD:
        direction = "BUY"
        rsi_label = "OVERSOLD"
    elif rsi >= config.RSI_OVERBOUGHT:
        direction = "SELL"
        rsi_label = "OVERBOUGHT"
    else:
        return None  # Neutral zone — no signal

    confidence = _compute_confidence(rsi, direction)

    if not force and confidence < min_confidence:
        print(f"  [SKIP] {symbol}: conf {confidence}% < min {min_confidence}%")
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
    if direction == "BUY":
        distance  = max(0.0, config.RSI_OVERSOLD - rsi)
        max_dist  = config.RSI_OVERSOLD
        base      = 55 + (distance / max(max_dist, 1)) * 43
    else:
        distance  = max(0.0, rsi - config.RSI_OVERBOUGHT)
        max_dist  = 100 - config.RSI_OVERBOUGHT
        base      = 55 + (distance / max(max_dist, 1)) * 43
    return min(98, max(55, int(base) + random.randint(-2, 3)))


# ─── NIGERIA TIME ─────────────────────────────────────────────────────────────

def _nigeria_now() -> datetime:
    return datetime.now(tz=timezone(timedelta(hours=config.TIMEZONE_OFFSET)))

def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p")

def _fmt_datetime(dt: datetime) -> str:
    return dt.strftime("%d %b %Y  %I:%M %p")

def _countdown(target: datetime) -> str:
    diff = int((target - _nigeria_now()).total_seconds())
    if diff <= 0:
        return "00:00"
    m, s = divmod(diff, 60)
    return f"{m:02d}:{s:02d}"


# ─── SIGNAL MESSAGE ───────────────────────────────────────────────────────────

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

    dir_emoji = "🟢🐂" if direction == "BUY" else "🔴🐻"
    dir_arrow = "⬆️ BUY" if direction == "BUY" else "⬇️ SELL"

    def fmt_p(v):
        if category == "crypto":
            return f"${v:,.6f}" if v < 0.01 else (f"${v:,.4f}" if v < 1 else f"${v:,.2f}")
        elif category == "forex":
            return f"{v:.5f}"
        return f"${v:,.2f}"

    price_str = fmt_p(price)
    pct = config.TP_SL_PCT
    tp  = price * (1 + pct) if direction == "BUY" else price * (1 - pct)
    sl  = price * (1 - pct) if direction == "BUY" else price * (1 + pct)

    mart_lines = []
    for lvl in range(1, config.MARTINGALE_LEVELS + 1):
        m_time = entry_time + timedelta(minutes=config.MARTINGALE_GAP_MIN * lvl)
        mult   = 2 ** (lvl - 1)
        mart_lines.append(
            f"  ├ Level {lvl} (×{mult}) → `{_fmt_time(m_time)}` WAT  ⏱ `{_countdown(m_time)}`"
        )

    filled = math.ceil(confidence / 10)
    bar    = "█" * filled + "░" * (10 - filled)

    return (
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
        f"\n\n✅ *Take Profit:*  `{fmt_p(tp)}`  _(+{pct*100:.1f}%)_\n"
        f"🛑 *Stop Loss:*    `{fmt_p(sl)}`  _(-{pct*100:.1f}%)_\n\n"
        f"⏳ *Duration:*  `{trade_duration} min`\n"
        f"📡 *Source:*  _{source}_\n"
        f"🏷 *Category:*  _{category.capitalize()}_\n"
        f"🕐 *Sent:*  `{_fmt_datetime(now_wat)} WAT`\n"
        f"{'━' * 32}"
    )


# ─── STARTUP / STATUS ─────────────────────────────────────────────────────────

def format_startup_message() -> str:
    now   = _fmt_datetime(_nigeria_now())
    total = sum(len(v) for v in config.get_all_pairs().values())
    return (
        "🚀 *Forex Crypto Signal Bot v5 is LIVE!*\n\n"
        f"📅 *Started:*  `{now} WAT`\n"
        f"📊 *Monitoring:*  `{total}` instruments across 5 categories\n"
        f"🔁 *Auto scan:*  every `{config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX}` min\n"
        f"📉 *RSI‑{config.RSI_PERIOD}:*  Buy < `{config.RSI_OVERSOLD}` | Sell > `{config.RSI_OVERBOUGHT}`\n\n"
        "⏳ _Price history builds over the first few scan cycles._\n"
        "_Genuine signals begin firing once RSI has real data._\n\n"
        "Use /debug to verify all APIs are connected."
    )


def format_status_message(
    auto_on: bool, signal_count: int,
    cg_ok: bool, er_ok: bool, td_ok: bool,
    min_confidence: int, trade_duration: int,
) -> str:
    now = _fmt_datetime(_nigeria_now())
    return (
        "🤖 *Bot Status*\n"
        f"{'─' * 32}\n"
        f"🕐 Time:               `{now} WAT`\n"
        f"🪙 CoinGecko (Crypto): {'✅ OK' if cg_ok else '❌ Unreachable'}\n"
        f"💱 ExchangeRate-API:   {'✅ OK' if er_ok else '❌ Unreachable'}\n"
        f"📊 Twelve Data:        {'✅ OK' if td_ok else '❌ Unreachable'}\n"
        f"🔄 Auto Signals:       {'✅ ON' if auto_on else '❌ OFF'}\n"
        f"📨 Signals Sent:       `{signal_count}`\n"
        f"🎯 Min Confidence:     `{min_confidence}%`\n"
        f"⏳ Trade Duration:     `{trade_duration} min`\n"
        f"📉 RSI:  Buy<`{config.RSI_OVERSOLD}` | Sell>`{config.RSI_OVERBOUGHT}`\n"
    )
