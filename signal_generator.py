# signal_generator.py  –  v6
# Key additions vs v5:
#   - Dynamic trade duration based on RSI strength
#   - OTC disclaimer on every OTC signal
#   - format_status_message updated for 3-source status

import math
import random
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

# ─── PRICE HISTORY ───────────────────────────────────────────────────────────
_price_history: dict[str, deque] = {}


def record_price(symbol: str, price: float) -> None:
    if symbol not in _price_history:
        _price_history[symbol] = deque(maxlen=100)
    _price_history[symbol].append(price)


def history_length(symbol: str) -> int:
    return len(_price_history.get(symbol, []))


def get_price_history(symbol: str) -> list:
    return list(_price_history.get(symbol, []))


# ─── RSI ─────────────────────────────────────────────────────────────────────

def calculate_rsi(prices: list, period: int = config.RSI_PERIOD) -> Optional[float]:
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
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


# ─── DYNAMIC DURATION ────────────────────────────────────────────────────────

def compute_dynamic_duration(rsi: float, direction: str) -> int:
    """
    Calculate the optimal trade duration in minutes based on RSI distance
    from the threshold.

    Logic:
      - Very extreme RSI (>15 pts past threshold) → market is deeply
        oversold/overbought, reversal likely fast → short duration (1-2 min)
      - Moderate RSI (8-15 pts past threshold) → clear signal, moderate
        reversal speed → medium duration (3-5 min)
      - Mild RSI (0-8 pts past threshold) → just crossed, slower reversal
        expected → longer duration (5-10 min)
    """
    if direction == "BUY":
        distance = config.RSI_OVERSOLD - rsi   # how far below 35
    else:
        distance = rsi - config.RSI_OVERBOUGHT  # how far above 65

    if distance > 15:
        # Extreme — fast reversal expected
        duration = random.randint(config.DURATION_EXTREME_MIN, config.DURATION_EXTREME_MAX)
        strength = "EXTREME"
    elif distance > 8:
        # Strong signal
        duration = random.randint(config.DURATION_STRONG_MIN, config.DURATION_STRONG_MAX)
        strength = "STRONG"
    else:
        # Mild — just crossed threshold
        duration = random.randint(config.DURATION_MILD_MIN, config.DURATION_MILD_MAX)
        strength = "MILD"

    return duration, strength


# ─── CONFIDENCE ──────────────────────────────────────────────────────────────

def _compute_confidence(rsi: float, direction: str) -> int:
    if direction == "BUY":
        distance = max(0.0, config.RSI_OVERSOLD - rsi)
        base     = 55 + (distance / max(config.RSI_OVERSOLD, 1)) * 43
    else:
        distance = max(0.0, rsi - config.RSI_OVERBOUGHT)
        base     = 55 + (distance / max(100 - config.RSI_OVERBOUGHT, 1)) * 43
    return min(98, max(55, int(base) + random.randint(-2, 3)))


# ─── SIGNAL EVALUATION ───────────────────────────────────────────────────────

def evaluate_signal(
    symbol:         str,
    current_price:  float,
    min_confidence: int,
    force:          bool = False,
) -> Optional[dict]:
    record_price(symbol, current_price)
    prices = get_price_history(symbol)
    n = len(prices)

    if n < config.MIN_PRICE_HISTORY:
        print(f"  [RSI] {symbol}: {n}/{config.MIN_PRICE_HISTORY} points – building history")
        return None

    rsi = calculate_rsi(prices)
    if rsi is None:
        return None

    print(f"  [RSI] {symbol}: price={current_price:.6g}  RSI={rsi:.2f}")

    if rsi <= config.RSI_OVERSOLD:
        direction, rsi_label = "BUY", "OVERSOLD"
    elif rsi >= config.RSI_OVERBOUGHT:
        direction, rsi_label = "SELL", "OVERBOUGHT"
    else:
        return None

    confidence = _compute_confidence(rsi, direction)

    if not force and confidence < min_confidence:
        print(f"  [SKIP] {symbol}: conf {confidence}% < min {min_confidence}%")
        return None

    duration, strength = compute_dynamic_duration(rsi, direction)

    return {
        "symbol":     symbol,
        "direction":  direction,
        "price":      current_price,
        "rsi":        rsi,
        "rsi_label":  rsi_label,
        "confidence": confidence,
        "duration":   duration,
        "strength":   strength,
    }


# ─── TIME HELPERS ─────────────────────────────────────────────────────────────

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
    signal:    dict,
    category:  str,
    pair_info: dict,
    source:    str,
) -> str:
    """
    Formats the full Telegram signal message.
    Duration is taken from signal dict (dynamically computed).
    OTC signals include a clear disclaimer.
    """
    now_wat    = _nigeria_now()
    entry_time = now_wat + timedelta(minutes=3)

    direction  = signal["direction"]
    price      = signal["price"]
    rsi        = signal["rsi"]
    rsi_label  = signal["rsi_label"]
    confidence = signal["confidence"]
    duration   = signal["duration"]
    strength   = signal["strength"]
    flag       = pair_info["flag"]
    pair_name  = pair_info["name"]
    symbol     = signal["symbol"]
    is_otc     = pair_info.get("otc", False)

    dir_emoji = "🟢🐂" if direction == "BUY" else "🔴🐻"
    dir_arrow = "⬆️ BUY" if direction == "BUY" else "⬇️ SELL"

    # Strength label for duration explanation
    strength_desc = {
        "EXTREME": f"RSI extremely {'oversold' if direction == 'BUY' else 'overbought'} — fast reversal",
        "STRONG":  f"RSI strongly {'oversold' if direction == 'BUY' else 'overbought'} — moderate reversal",
        "MILD":    f"RSI mildly {'oversold' if direction == 'BUY' else 'overbought'} — slower reversal",
    }.get(strength, "")

    def fmt_p(v):
        if category == "crypto":
            return f"${v:,.6f}" if v < 0.01 else (f"${v:,.4f}" if v < 1 else f"${v:,.2f}")
        elif category == "forex":
            return f"{v:.5f}"
        return f"${v:,.2f}"

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

    # OTC disclaimer block
    otc_block = ""
    if is_otc:
        otc_block = (
            "\n⚠️ *OTC NOTICE:*\n"
            "_This is an OTC instrument. Price shown is from the\n"
            "underlying real market pair. Pocket Option OTC prices\n"
            "may differ slightly from this feed._\n"
        )

    return (
        f"{'━' * 32}\n"
        f"{flag}  *{pair_name}*\n"
        f"{'━' * 32}\n"
        f"{dir_emoji}  *{dir_arrow}*\n\n"
        f"💰 *Live Price:*  `{fmt_p(price)}`\n"
        f"⏰ *Entry Time:*  `{_fmt_time(entry_time)}` WAT  ⏱ `{_countdown(entry_time)}`\n\n"
        f"📊 *RSI‑{config.RSI_PERIOD}:*  `{rsi:.2f}`  →  _{rsi_label}_\n"
        f"📶 *Signal Strength:*  _{strength}_\n\n"
        f"🎯 *Confidence:*  `{confidence}%`\n"
        f"`[{bar}]`\n\n"
        f"⏳ *Trade Duration:*  `{duration} min`\n"
        f"_({strength_desc})_\n\n"
        f"📈 *Martingale Ladder:*\n"
        + "\n".join(mart_lines) +
        f"\n\n✅ *Take Profit:*  `{fmt_p(tp)}`  _(+{pct*100:.1f}%)_\n"
        f"🛑 *Stop Loss:*    `{fmt_p(sl)}`  _(-{pct*100:.1f}%)_\n"
        f"{otc_block}\n"
        f"📡 *Source:*  _{source}_\n"
        f"🏷 *Category:*  _{category.capitalize()}{'  •  OTC' if is_otc else ''}_\n"
        f"🕐 *Sent:*  `{_fmt_datetime(now_wat)} WAT`\n"
        f"{'━' * 32}"
    )


# ─── STARTUP / STATUS ─────────────────────────────────────────────────────────

def format_startup_message() -> str:
    now   = _fmt_datetime(_nigeria_now())
    total = sum(len(v) for v in config.get_all_pairs().values())
    otc_count = sum(
        1 for _, pairs in config.get_all_pairs().items()
        for info in pairs.values() if info.get("otc")
    )
    return (
        "🚀 *Forex Crypto Signal Bot v6 is LIVE!*\n\n"
        f"📅 *Started:*  `{now} WAT`\n"
        f"📊 *Monitoring:*  `{total}` instruments\n"
        f"🔄 *OTC pairs:*  `{otc_count}` included\n"
        f"🔁 *Auto scan:*  every `{config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX}` min\n"
        f"📉 *RSI‑{config.RSI_PERIOD}:*  Buy < `{config.RSI_OVERSOLD}` | Sell > `{config.RSI_OVERBOUGHT}`\n"
        f"⏱ *Duration:*  Dynamic (1–10 min based on RSI strength)\n\n"
        "⚠️ _OTC prices use underlying market feed._\n"
        "_Pocket Option OTC prices may differ slightly._\n\n"
        "Use /history to track RSI build-up progress.\n"
        "Use /debug to verify API connections."
    )


def format_status_message(
    auto_on: bool, signal_count: int,
    cg_ok: bool, er_ok: bool, td_ok: bool,
    min_confidence: int,
) -> str:
    now = _fmt_datetime(_nigeria_now())
    return (
        "🤖 *Bot Status*\n"
        f"{'─' * 32}\n"
        f"🕐 Time:               `{now} WAT`\n"
        f"🪙 CoinGecko (Crypto): {'✅ OK' if cg_ok else '❌ Down'}\n"
        f"💱 ExchangeRate-API:   {'✅ OK' if er_ok else '❌ Down'}\n"
        f"📊 Twelve Data:        {'✅ OK' if td_ok else '❌ Down'}\n"
        f"🔄 Auto Signals:       {'✅ ON' if auto_on else '❌ OFF'}\n"
        f"📨 Signals Sent:       `{signal_count}`\n"
        f"🎯 Min Confidence:     `{min_confidence}%`\n"
        f"⏱ Duration:           Dynamic (RSI-based)\n"
        f"📉 RSI:  Buy<`{config.RSI_OVERSOLD}` | Sell>`{config.RSI_OVERBOUGHT}`\n"
        f"🚦 Max/scan:           `{config.MAX_SIGNALS_PER_SCAN}`\n"
    )
