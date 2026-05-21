# signal_generator.py  –  v10
#
# SIGNAL ENGINE OVERHAUL
# ──────────────────────
# Previous versions used RSI alone → ~20% win rate.
# This version requires 4 out of 5 indicators to confirm before firing.
#
# The 5 indicators:
#   1. RSI (14)              — oversold/overbought baseline
#   2. Stochastic (14,3,3)   — secondary overbought/oversold (matches PO chart)
#   3. MACD (12,26,9)        — momentum direction confirmation
#   4. Bollinger Bands (20,2)— price at/outside band = extreme move
#   5. EMA Cross (9/21)      — trend context filter
#
# A signal fires ONLY when score >= MIN_SCORE (default 4/5).
# The confidence shown is based on the score, not arbitrary RSI distance.
# Duration is driven by combined indicator strength, not RSI alone.

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
        _price_history[symbol] = deque(maxlen=200)
    _price_history[symbol].append(price)


def history_length(symbol: str) -> int:
    return len(_price_history.get(symbol, []))


def get_price_history(symbol: str) -> list:
    return list(_price_history.get(symbol, []))


# ─── INDICATOR CALCULATIONS ──────────────────────────────────────────────────

def _ema(prices: list, period: int) -> Optional[float]:
    """Exponential Moving Average — returns latest EMA value."""
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period   # seed with SMA
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    return ema


def _ema_series(prices: list, period: int) -> list:
    """Return full EMA series for MACD calculation."""
    if len(prices) < period:
        return []
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    series = [ema]
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
        series.append(ema)
    return series


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
    return round(100.0 - (100.0 / (1.0 + avg_gain / avg_loss)), 2)


def calculate_stochastic(prices: list) -> tuple[Optional[float], Optional[float]]:
    """
    Stochastic Oscillator (14, 3, 3).
    Returns (%K, %D) or (None, None).
    Matches the Stochastic shown on Pocket Option charts.
    """
    k_period = config.STOCH_K_PERIOD
    d_period = config.STOCH_D_PERIOD
    if len(prices) < k_period + d_period:
        return None, None

    # Calculate raw %K values
    k_values = []
    for i in range(k_period - 1, len(prices)):
        window   = prices[i - k_period + 1 : i + 1]
        low_min  = min(window)
        high_max = max(window)
        if high_max == low_min:
            k_values.append(50.0)
        else:
            k_values.append(100 * (prices[i] - low_min) / (high_max - low_min))

    if len(k_values) < d_period:
        return None, None

    # Smooth %K with 3-period SMA → gives smoothed %K
    smoothed_k = []
    for i in range(d_period - 1, len(k_values)):
        smoothed_k.append(sum(k_values[i - d_period + 1: i + 1]) / d_period)

    if len(smoothed_k) < d_period:
        return None, None

    # %D = 3-period SMA of smoothed %K
    d = sum(smoothed_k[-d_period:]) / d_period

    return round(smoothed_k[-1], 2), round(d, 2)


def calculate_macd(prices: list) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    MACD (12, 26, 9).
    Returns (macd_line, signal_line, histogram) or (None, None, None).
    """
    fast = config.MACD_FAST
    slow = config.MACD_SLOW
    sig  = config.MACD_SIGNAL

    if len(prices) < slow + sig:
        return None, None, None

    ema_fast_series = _ema_series(prices, fast)
    ema_slow_series = _ema_series(prices, slow)

    # Align series lengths
    diff = len(ema_fast_series) - len(ema_slow_series)
    macd_series = [
        ema_fast_series[diff + i] - ema_slow_series[i]
        for i in range(len(ema_slow_series))
    ]

    if len(macd_series) < sig:
        return None, None, None

    # Signal line = EMA of MACD series
    k = 2 / (sig + 1)
    signal_line = sum(macd_series[:sig]) / sig
    for val in macd_series[sig:]:
        signal_line = val * k + signal_line * (1 - k)

    macd_val  = macd_series[-1]
    histogram = macd_val - signal_line
    return round(macd_val, 6), round(signal_line, 6), round(histogram, 6)


def calculate_bollinger(prices: list) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Bollinger Bands (20, 2).
    Returns (upper_band, middle_band, lower_band) or (None, None, None).
    """
    period = config.BB_PERIOD
    std    = config.BB_STD_DEV
    if len(prices) < period:
        return None, None, None
    window = prices[-period:]
    mid    = sum(window) / period
    variance = sum((p - mid) ** 2 for p in window) / period
    band_width = std * math.sqrt(variance)
    return round(mid + band_width, 6), round(mid, 6), round(mid - band_width, 6)


# ─── MULTI-INDICATOR SCORER ──────────────────────────────────────────────────

def score_signal(prices: list, direction: str) -> tuple[int, dict]:
    """
    Score the signal from 0–5 based on how many indicators confirm.
    Returns (score, details_dict).

    BUY confirmations:
      1. RSI <= RSI_OVERSOLD (30)
      2. Stochastic %K <= STOCH_OVERSOLD (20)
      3. MACD histogram turning positive (histogram > prev_histogram)
      4. Price at or below lower Bollinger Band
      5. Price below EMA_SLOW (mean reversion setup)

    SELL confirmations:
      1. RSI >= RSI_OVERBOUGHT (70)
      2. Stochastic %K >= STOCH_OVERBOUGHT (80)
      3. MACD histogram turning negative (histogram < prev_histogram)
      4. Price at or above upper Bollinger Band
      5. Price above EMA_SLOW (mean reversion setup)
    """
    score   = 0
    details = {}
    current = prices[-1]

    # 1. RSI
    rsi = calculate_rsi(prices)
    details["rsi"] = rsi
    if rsi is not None:
        if direction == "BUY"  and rsi <= config.RSI_OVERSOLD:
            score += 1
            details["rsi_ok"] = True
        elif direction == "SELL" and rsi >= config.RSI_OVERBOUGHT:
            score += 1
            details["rsi_ok"] = True
        else:
            details["rsi_ok"] = False
    else:
        details["rsi_ok"] = None

    # 2. Stochastic
    stoch_k, stoch_d = calculate_stochastic(prices)
    details["stoch_k"] = stoch_k
    details["stoch_d"] = stoch_d
    if stoch_k is not None:
        if direction == "BUY"  and stoch_k <= config.STOCH_OVERSOLD:
            score += 1
            details["stoch_ok"] = True
        elif direction == "SELL" and stoch_k >= config.STOCH_OVERBOUGHT:
            score += 1
            details["stoch_ok"] = True
        else:
            details["stoch_ok"] = False
    else:
        details["stoch_ok"] = None

    # 3. MACD momentum (histogram direction)
    macd, macd_sig, histogram = calculate_macd(prices)
    details["macd"]      = macd
    details["macd_sig"]  = macd_sig
    details["histogram"] = histogram
    if histogram is not None and len(prices) >= 2:
        # Compare current histogram to previous bar's histogram
        prev_prices = prices[:-1]
        _, _, prev_hist = calculate_macd(prev_prices)
        details["prev_histogram"] = prev_hist
        if prev_hist is not None:
            if direction == "BUY"  and histogram > prev_hist:   # histogram rising
                score += 1
                details["macd_ok"] = True
            elif direction == "SELL" and histogram < prev_hist:  # histogram falling
                score += 1
                details["macd_ok"] = True
            else:
                details["macd_ok"] = False
        else:
            details["macd_ok"] = None
    else:
        details["macd_ok"] = None

    # 4. Bollinger Bands
    bb_upper, bb_mid, bb_lower = calculate_bollinger(prices)
    details["bb_upper"] = bb_upper
    details["bb_mid"]   = bb_mid
    details["bb_lower"] = bb_lower
    if bb_upper is not None:
        if direction == "BUY"  and current <= bb_lower:
            score += 1
            details["bb_ok"] = True
        elif direction == "SELL" and current >= bb_upper:
            score += 1
            details["bb_ok"] = True
        else:
            details["bb_ok"] = False
    else:
        details["bb_ok"] = None

    # 5. EMA trend context
    ema_slow = _ema(prices, config.EMA_SLOW)
    ema_fast = _ema(prices, config.EMA_FAST)
    details["ema_fast"] = ema_fast
    details["ema_slow"] = ema_slow
    if ema_slow is not None and ema_fast is not None:
        if direction == "BUY"  and current < ema_slow:  # below slow EMA = mean reversion zone
            score += 1
            details["ema_ok"] = True
        elif direction == "SELL" and current > ema_slow: # above slow EMA = mean reversion zone
            score += 1
            details["ema_ok"] = True
        else:
            details["ema_ok"] = False
    else:
        details["ema_ok"] = None

    return score, details


# ─── DYNAMIC DURATION ────────────────────────────────────────────────────────

def compute_dynamic_duration(score: int, rsi: float, direction: str) -> tuple:
    """
    Duration now driven by combined score + RSI extremity.
    Higher score + more extreme RSI = shorter, more confident trade.
    """
    rsi_distance = (
        config.RSI_OVERSOLD - rsi
        if direction == "BUY" and rsi
        else (rsi - config.RSI_OVERBOUGHT if rsi else 0)
    )

    if score == 5 and rsi_distance > 10:
        duration = random.randint(1, 3)
        strength = "PERFECT"
        reason   = "All 5 indicators aligned + deep RSI extreme"
    elif score == 5:
        duration = random.randint(2, 5)
        strength = "VERY STRONG"
        reason   = "All 5 indicators aligned"
    elif score == 4 and rsi_distance > 10:
        duration = random.randint(3, 8)
        strength = "STRONG"
        reason   = "4/5 indicators + deep RSI extreme"
    elif score == 4:
        duration = random.randint(5, 15)
        strength = "STRONG"
        reason   = "4/5 indicators confirmed"
    else:
        duration = random.randint(10, 25)
        strength = "MODERATE"
        reason   = f"{score}/5 indicators confirmed"

    return duration, strength, reason


# ─── SIGNAL EVALUATION ───────────────────────────────────────────────────────

def evaluate_signal(
    symbol:         str,
    current_price:  float,
    min_confidence: int,
    force:          bool = False,
) -> Optional[dict]:
    """
    Records price and evaluates all 5 indicators.
    Returns a signal dict only when score >= MIN_SCORE.
    """
    record_price(symbol, current_price)
    prices = get_price_history(symbol)
    n = len(prices)

    if n < config.MIN_PRICE_HISTORY:
        print(f"  [SCORE] {symbol}: {n}/{config.MIN_PRICE_HISTORY} pts – building history")
        return None

    # Determine direction candidate from RSI first
    rsi = calculate_rsi(prices)
    if rsi is None:
        return None

    if rsi <= config.RSI_OVERSOLD:
        direction = "BUY"
    elif rsi >= config.RSI_OVERBOUGHT:
        direction = "SELL"
    else:
        # RSI neutral — no signal possible regardless of other indicators
        return None

    # Now score all 5 indicators for that direction
    score, details = score_signal(prices, direction)

    print(
        f"  [SCORE] {symbol}: RSI={rsi:.1f}  score={score}/5  "
        f"dir={direction}  "
        f"[RSI={'✓' if details.get('rsi_ok') else '✗'} "
        f"Stoch={'✓' if details.get('stoch_ok') else '✗'} "
        f"MACD={'✓' if details.get('macd_ok') else '✗'} "
        f"BB={'✓' if details.get('bb_ok') else '✗'} "
        f"EMA={'✓' if details.get('ema_ok') else '✗'}]"
    )

    if score < config.MIN_SCORE:
        print(f"  [SKIP] {symbol}: score {score} < min {config.MIN_SCORE}")
        return None

    # Confidence scales with score: 4/5=75%, 5/5=90%+
    base_conf = 60 + (score / 5) * 35
    confidence = min(98, max(60, int(base_conf) + random.randint(-3, 4)))

    if not force and confidence < min_confidence:
        print(f"  [SKIP] {symbol}: conf {confidence}% < min {min_confidence}%")
        return None

    # RSI label
    rsi_label = "OVERSOLD" if direction == "BUY" else "OVERBOUGHT"

    duration, strength, reason = compute_dynamic_duration(score, rsi, direction)
    entry_lead = random.randint(config.ENTRY_LEAD_MIN, config.ENTRY_LEAD_MAX)

    return {
        "symbol":     symbol,
        "direction":  direction,
        "price":      current_price,
        "rsi":        rsi,
        "rsi_label":  rsi_label,
        "confidence": confidence,
        "duration":   duration,
        "strength":   strength,
        "reason":     reason,
        "entry_lead": entry_lead,
        "score":      score,
        "details":    details,
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


# ─── MARTINGALE BUILDER ───────────────────────────────────────────────────────

def build_martingale_lines(entry_time: datetime, duration: int) -> list:
    lines = []
    for lvl in range(1, config.MARTINGALE_LEVELS + 1):
        level_start = entry_time + timedelta(minutes=duration * (lvl - 1))
        level_end   = level_start + timedelta(minutes=duration)
        multiplier  = 2 ** (lvl - 1)
        lines.append(
            f"  {'├' if lvl < config.MARTINGALE_LEVELS else '└'} "
            f"*Level {lvl}* (×{multiplier} stake)\n"
            f"     ▶ Enter:  `{_fmt_time(level_start)}` WAT  ⏱ `{_countdown(level_start)}`\n"
            f"     ⏹ Expire: `{_fmt_time(level_end)}` WAT  ⏱ `{_countdown(level_end)}`"
        )
    return lines


# ─── INDICATOR SUMMARY LINE ───────────────────────────────────────────────────

def _indicator_summary(details: dict) -> str:
    """Build a compact one-line indicator status for the signal message."""
    def mark(key):
        val = details.get(key)
        if val is True:
            return "✅"
        elif val is False:
            return "❌"
        return "⏳"

    rsi_val   = f"{details['rsi']:.1f}"   if details.get("rsi")   else "N/A"
    stoch_val = f"{details['stoch_k']:.1f}" if details.get("stoch_k") else "N/A"
    macd_val  = f"{details['histogram']:.5f}" if details.get("histogram") else "N/A"
    bb_note   = "at band" if details.get("bb_ok") else "inside"
    ema_note  = "below EMA" if details.get("ema_ok") and details.get("ema_ok") else "above EMA"

    return (
        f"{mark('rsi_ok')} RSI `{rsi_val}`  "
        f"{mark('stoch_ok')} Stoch `{stoch_val}`  "
        f"{mark('macd_ok')} MACD `{macd_val}`  "
        f"{mark('bb_ok')} BB {bb_note}  "
        f"{mark('ema_ok')} EMA"
    )


# ─── SIGNAL MESSAGE ───────────────────────────────────────────────────────────

def format_signal_message(
    signal:    dict,
    category:  str,
    pair_info: dict,
    source:    str,
) -> str:
    now_wat     = _nigeria_now()
    entry_lead  = signal["entry_lead"]
    entry_time  = now_wat + timedelta(minutes=entry_lead)
    expiry_time = entry_time + timedelta(minutes=signal["duration"])

    direction  = signal["direction"]
    price      = signal["price"]
    rsi        = signal["rsi"]
    rsi_label  = signal["rsi_label"]
    confidence = signal["confidence"]
    duration   = signal["duration"]
    strength   = signal["strength"]
    reason     = signal["reason"]
    score      = signal["score"]
    details    = signal["details"]
    flag       = pair_info["flag"]
    pair_name  = pair_info["name"]

    dir_emoji = "🟢🐂" if direction == "BUY" else "🔴🐻"
    dir_arrow = "⬆️ BUY" if direction == "BUY" else "⬇️ SELL"

    def fmt_p(v):
        if category == "crypto":
            return f"${v:,.6f}" if v < 0.01 else (f"${v:,.4f}" if v < 1 else f"${v:,.2f}")
        elif category == "forex":
            return f"{v:.5f}"
        return f"${v:,.2f}"

    pct = config.TP_SL_PCT
    tp  = price * (1 + pct) if direction == "BUY" else price * (1 - pct)
    sl  = price * (1 - pct) if direction == "BUY" else price * (1 + pct)

    # Score stars
    stars = "⭐" * score + "☆" * (5 - score)

    # Confidence bar
    filled = math.ceil(confidence / 10)
    bar    = "█" * filled + "░" * (10 - filled)

    # Duration label
    if duration <= 3:
        dur_label = f"{duration} min ⚡"
    elif duration <= 10:
        dur_label = f"{duration} min 📊"
    elif duration <= 25:
        dur_label = f"{duration} min 🕐"
    else:
        dur_label = f"{duration} min 🐢"

    # Martingale block
    mart_lines = build_martingale_lines(entry_time, duration)

    otc_block = ""

    # Indicator summary
    ind_summary = _indicator_summary(details)

    return (
        f"{'━' * 32}\n"
        f"{flag}  *{pair_name}*\n"
        f"{'━' * 32}\n"
        f"{dir_emoji}  *{dir_arrow}*\n\n"
        f"💰 *Price:*  `{fmt_p(price)}`\n"
        f"📡 *Source:* _{source}_\n\n"
        f"{'─' * 32}\n"
        f"📊 *Indicator Score:*  {stars}  `{score}/5`\n"
        f"{ind_summary}\n\n"
        f"🎯 *Confidence:*  `{confidence}%`\n"
        f"`[{bar}]`\n\n"
        f"📶 *Signal Strength:*  _{strength}_\n"
        f"_↳ {reason}_\n\n"
        f"{'─' * 32}\n"
        f"🕐 *Signal sent:*  `{_fmt_datetime(now_wat)} WAT`\n"
        f"🟢 *Entry time:*   `{_fmt_time(entry_time)}` WAT  ⏱ `{_countdown(entry_time)}`\n"
        f"🔴 *Expiry time:*  `{_fmt_time(expiry_time)}` WAT  ⏱ `{_countdown(expiry_time)}`\n"
        f"⏳ *Duration:*     `{dur_label}`\n\n"
        f"{'─' * 32}\n"
        f"📈 *Martingale* _(2 levels, gap = duration)_\n"
        + "\n".join(mart_lines) +
        f"\n\n{'─' * 32}\n"
        f"✅ *Take Profit:*  `{fmt_p(tp)}`\n"
        f"🛑 *Stop Loss:*    `{fmt_p(sl)}`\n"
        f"{otc_block}"
        f"🏷 *Category:*  _{category.capitalize()}_\n"
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
        "🚀 *Forex Crypto Signal Bot v10 is LIVE!*\n\n"
        f"📅 *Started:*  `{now} WAT`\n"
        f"📊 *Pairs:*  `{total}` instruments ({otc_count} OTC)\n\n"
        f"🔬 *Signal Engine:*  5-Indicator System\n"
        f"  ✅ RSI ({config.RSI_PERIOD}) — oversold/overbought\n"
        f"  ✅ Stochastic ({config.STOCH_K_PERIOD},{config.STOCH_D_PERIOD},{config.STOCH_D_PERIOD}) — secondary confirmation\n"
        f"  ✅ MACD ({config.MACD_FAST},{config.MACD_SLOW},{config.MACD_SIGNAL}) — momentum direction\n"
        f"  ✅ Bollinger Bands ({config.BB_PERIOD},{config.BB_STD_DEV}) — price extremes\n"
        f"  ✅ EMA ({config.EMA_FAST}/{config.EMA_SLOW}) — trend context\n\n"
        f"🎯 *Fires only when {config.MIN_SCORE}/5 indicators confirm*\n"
        f"📊 *History needed:* {config.MIN_PRICE_HISTORY} points per pair\n"
        f"⏰ *Ready in:* ~{config.MIN_PRICE_HISTORY * config.SCAN_INTERVAL_MIN // 60}h "
        f"{(config.MIN_PRICE_HISTORY * config.SCAN_INTERVAL_MIN) % 60}min at 10-min scans\n"
        f"⏱ *Duration:* Dynamic (score + RSI based)\n"
        f"📈 *Martingale:* 2 levels, gap = trade duration\n\n"
        "⚠️ _OTC prices use underlying market feed._\n\n"
        "Use /history to track indicator readiness.\n"
        "Use /debug to verify API connections."
    )


def format_status_message(
    auto_on: bool, signal_count: int,
    cg_ok: bool, er_ok: bool, td_ok: bool,
    min_confidence: int,
) -> str:
    now = _fmt_datetime(_nigeria_now())
    return (
        "🤖 *Bot Status  —  v9*\n"
        f"{'─' * 32}\n"
        f"🕐 Time:               `{now} WAT`\n"
        f"🪙 CoinGecko (Crypto): {'✅ OK' if cg_ok else '❌ Down'}\n"
        f"💱 ExchangeRate-API:   {'✅ OK' if er_ok else '❌ Down'}\n"
        f"📊 Twelve Data:        {'✅ OK' if td_ok else '❌ Down'}\n"
        f"🔄 Auto Signals:       {'✅ ON' if auto_on else '❌ OFF'}\n"
        f"📨 Signals Sent:       `{signal_count}`\n"
        f"🎯 Min Confidence:     `{min_confidence}%`\n"
        f"🔬 Signal Engine:      5-indicator, min {config.MIN_SCORE}/5\n"
        f"⏱ Duration:           Dynamic (score + RSI based)\n"
        f"📈 Martingale:         2 levels, gap = duration\n"
        f"🚦 Max signals/scan:   `{config.MAX_SIGNALS_PER_SCAN}`\n"
        f"📉 RSI:  Buy≤`{config.RSI_OVERSOLD}` | Sell≥`{config.RSI_OVERBOUGHT}`\n"
    )
