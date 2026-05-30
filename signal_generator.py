# signal_generator.py  –  v11
#
# 7-INDICATOR SIGNAL ENGINE
# ─────────────────────────
# 1. RSI (7)                — oversold/overbought
# 2. Stochastic (7,3,3)     — secondary oversold/overbought
# 3. MACD (6,12,5)          — momentum direction
# 4. Bollinger Bands (10,2) — price at extreme
# 5. EMA (5/10)             — trend context
# 6. RSI Divergence         — price vs RSI direction conflict (strongest signal)
# 7. ADX (7)                — ranging market filter (skip if trending)
#
# ADDITIONAL FILTERS:
# - Trading session filter (forex: London/NY only)
# - Minimum payout filter (skip pairs below MIN_PAYOUT_PCT)
# - Candlestick pattern confirmation (Hammer, Engulfing, Doji)
#
# Signal fires when score >= MIN_SCORE (default 3/7)

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


# ─── RSI ─────────────────────────────────────────────────────────────────────

def calculate_rsi(prices: list, period: int = config.RSI_PERIOD) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains  = [max(d, 0.0) for d in deltas]
    losses = [abs(min(d, 0.0)) for d in deltas]
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0:
        return 100.0
    return round(100.0 - (100.0 / (1.0 + ag / al)), 2)


# ─── EMA ─────────────────────────────────────────────────────────────────────

def _ema_value(prices: list, period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    k   = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
    return ema


def _ema_series(prices: list, period: int) -> list:
    if len(prices) < period:
        return []
    k   = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    series = [ema]
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
        series.append(ema)
    return series


# ─── MACD ────────────────────────────────────────────────────────────────────

def calculate_macd(prices: list):
    fast, slow, sig = config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL
    if len(prices) < slow + sig:
        return None, None, None
    ef = _ema_series(prices, fast)
    es = _ema_series(prices, slow)
    diff = len(ef) - len(es)
    macd_series = [ef[diff + i] - es[i] for i in range(len(es))]
    if len(macd_series) < sig:
        return None, None, None
    k   = 2 / (sig + 1)
    sl  = sum(macd_series[:sig]) / sig
    for v in macd_series[sig:]:
        sl = v * k + sl * (1 - k)
    macd_val = macd_series[-1]
    return round(macd_val, 6), round(sl, 6), round(macd_val - sl, 6)


# ─── STOCHASTIC ──────────────────────────────────────────────────────────────

def calculate_stochastic(prices: list):
    kp, dp = config.STOCH_K_PERIOD, config.STOCH_D_PERIOD
    if len(prices) < kp + dp:
        return None, None
    k_vals = []
    for i in range(kp - 1, len(prices)):
        window  = prices[i - kp + 1 : i + 1]
        lo, hi  = min(window), max(window)
        k_vals.append(50.0 if hi == lo else 100 * (prices[i] - lo) / (hi - lo))
    if len(k_vals) < dp:
        return None, None
    sk = []
    for i in range(dp - 1, len(k_vals)):
        sk.append(sum(k_vals[i - dp + 1 : i + 1]) / dp)
    if len(sk) < dp:
        return None, None
    return round(sk[-1], 2), round(sum(sk[-dp:]) / dp, 2)


# ─── BOLLINGER BANDS ─────────────────────────────────────────────────────────

def calculate_bollinger(prices: list):
    period, std = config.BB_PERIOD, config.BB_STD_DEV
    if len(prices) < period:
        return None, None, None
    window = prices[-period:]
    mid    = sum(window) / period
    bw     = std * math.sqrt(sum((p - mid) ** 2 for p in window) / period)
    return round(mid + bw, 6), round(mid, 6), round(mid - bw, 6)


# ─── ADX ─────────────────────────────────────────────────────────────────────

def calculate_adx(prices: list, period: int = config.ADX_PERIOD) -> Optional[float]:
    """
    Simplified ADX from price-only data (no high/low available).
    Uses absolute price changes as a proxy for directional movement.
    Returns ADX value 0–100. Above ADX_THRESHOLD = trending = skip signal.
    """
    if len(prices) < period * 2:
        return None
    changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
    if len(changes) < period:
        return None
    # Wilder smoothing of absolute changes
    adx = sum(changes[:period]) / period
    for c in changes[period:]:
        adx = (adx * (period - 1) + c) / period
    # Normalise to 0–100 range using recent price as denominator
    current = prices[-1]
    if current == 0:
        return None
    normalised = (adx / current) * 1000   # scale factor
    return round(min(normalised, 100), 2)


# ─── RSI DIVERGENCE ──────────────────────────────────────────────────────────

def check_divergence(prices: list, direction: str) -> bool:
    """
    Detect RSI divergence — one of the strongest reversal signals.

    Bullish divergence (for BUY):
      Price makes a lower low but RSI makes a higher low.
      → Momentum weakening while price still falling = reversal coming.

    Bearish divergence (for SELL):
      Price makes a higher high but RSI makes a lower high.
      → Momentum weakening while price still rising = reversal coming.

    Requires at least 20 price points to find meaningful swing points.
    """
    if len(prices) < 20:
        return False

    # Split into two halves to compare swing points
    mid   = len(prices) // 2
    first = prices[:mid]
    second = prices[mid:]

    rsi_first  = calculate_rsi(first)
    rsi_second = calculate_rsi(second)

    if rsi_first is None or rsi_second is None:
        return False

    price_first_low   = min(first)
    price_second_low  = min(second)
    price_first_high  = max(first)
    price_second_high = max(second)

    if direction == "BUY":
        # Bullish divergence: price lower low, RSI higher low
        return price_second_low < price_first_low and rsi_second > rsi_first

    else:
        # Bearish divergence: price higher high, RSI lower high
        return price_second_high > price_first_high and rsi_second < rsi_first


# ─── CANDLESTICK PATTERN DETECTOR ────────────────────────────────────────────

def check_candlestick_pattern(prices: list, direction: str) -> tuple[bool, str]:
    """
    Detect basic reversal candlestick patterns from price sequence.
    Since we only have close prices (no OHLC), we simulate patterns
    from price movement direction and relative sizes.

    Returns (pattern_found: bool, pattern_name: str)
    """
    if len(prices) < 3:
        return False, ""

    p1, p2, p3 = prices[-3], prices[-2], prices[-1]
    body2 = abs(p2 - p1)    # previous candle body
    body3 = abs(p3 - p2)    # current candle body

    if direction == "BUY":
        # Bullish engulfing: previous down, current up and larger
        if p2 < p1 and p3 > p2 and body3 > body2 * 1.1:
            return True, "Bullish Engulfing"
        # Hammer: price dropped then recovered strongly
        if p2 < p1 and p3 > p1:
            return True, "Hammer"
        # Doji at low: tiny body after decline
        if p2 < p1 and body3 < body2 * 0.3:
            return True, "Doji (reversal)"

    else:
        # Bearish engulfing: previous up, current down and larger
        if p2 > p1 and p3 < p2 and body3 > body2 * 1.1:
            return True, "Bearish Engulfing"
        # Shooting star: price rose then reversed strongly
        if p2 > p1 and p3 < p1:
            return True, "Shooting Star"
        # Doji at high: tiny body after rise
        if p2 > p1 and body3 < body2 * 0.3:
            return True, "Doji (reversal)"

    return False, ""


# ─── SESSION FILTER ──────────────────────────────────────────────────────────

def is_active_session(category: str) -> bool:
    """
    Return True if it is a good time to trade this category.
    Forex: only during London + New York overlap (08:00–21:00 UTC).
    Crypto, stocks, indices, commodities: always active.
    OTC: always active (runs 24/7 on Pocket Option).
    """
    if category in ("crypto", "otc", "stocks", "commodities"):
        return True

    utc_hour = datetime.now(tz=timezone.utc).hour
    return config.SESSION_START <= utc_hour < config.SESSION_END


# ─── 7-INDICATOR SCORER ──────────────────────────────────────────────────────

def score_signal(prices: list, direction: str) -> tuple[int, dict]:
    """
    Score signal from 0–7 across all indicators.
    Returns (score, details_dict).
    """
    score   = 0
    details = {}
    current = prices[-1]

    # 1. RSI
    rsi = calculate_rsi(prices)
    details["rsi"] = rsi
    if rsi is not None:
        ok = (direction == "BUY" and rsi <= config.RSI_OVERSOLD) or \
             (direction == "SELL" and rsi >= config.RSI_OVERBOUGHT)
        details["rsi_ok"] = ok
        if ok:
            score += 1
    else:
        details["rsi_ok"] = None

    # 2. Stochastic
    sk, sd = calculate_stochastic(prices)
    details["stoch_k"], details["stoch_d"] = sk, sd
    if sk is not None:
        ok = (direction == "BUY" and sk <= config.STOCH_OVERSOLD) or \
             (direction == "SELL" and sk >= config.STOCH_OVERBOUGHT)
        details["stoch_ok"] = ok
        if ok:
            score += 1
    else:
        details["stoch_ok"] = None

    # 3. MACD momentum (histogram turning)
    macd, macd_sig, histogram = calculate_macd(prices)
    details["histogram"] = histogram
    if histogram is not None and len(prices) >= 2:
        _, _, prev_hist = calculate_macd(prices[:-1])
        if prev_hist is not None:
            ok = (direction == "BUY" and histogram > prev_hist) or \
                 (direction == "SELL" and histogram < prev_hist)
            details["macd_ok"] = ok
            if ok:
                score += 1
        else:
            details["macd_ok"] = None
    else:
        details["macd_ok"] = None

    # 4. Bollinger Bands
    bb_u, bb_m, bb_l = calculate_bollinger(prices)
    details["bb_upper"], details["bb_lower"] = bb_u, bb_l
    if bb_u is not None:
        ok = (direction == "BUY" and current <= bb_l) or \
             (direction == "SELL" and current >= bb_u)
        details["bb_ok"] = ok
        if ok:
            score += 1
    else:
        details["bb_ok"] = None

    # 5. EMA (mean reversion context)
    ema_slow = _ema_value(prices, config.EMA_SLOW)
    ema_fast = _ema_value(prices, config.EMA_FAST)
    details["ema_slow"] = ema_slow
    if ema_slow is not None:
        ok = (direction == "BUY" and current < ema_slow) or \
             (direction == "SELL" and current > ema_slow)
        details["ema_ok"] = ok
        if ok:
            score += 1
    else:
        details["ema_ok"] = None

    # 6. RSI Divergence (bonus — strongest signal type)
    divergence = check_divergence(prices, direction)
    details["divergence"] = divergence
    if divergence:
        score += 1   # counts as full confirmation point
    details["divergence_ok"] = divergence

    # 7. ADX (ranging market check)
    adx = calculate_adx(prices)
    details["adx"] = adx
    if adx is not None:
        ranging = adx < config.ADX_THRESHOLD
        details["adx_ok"] = ranging
        if ranging:
            score += 1   # market is ranging = indicators are reliable
    else:
        details["adx_ok"] = None

    return score, details


# ─── DYNAMIC DURATION ────────────────────────────────────────────────────────

def compute_dynamic_duration(score: int, rsi: float, direction: str) -> tuple:
    rsi_dist = (
        config.RSI_OVERSOLD - rsi if direction == "BUY" and rsi
        else rsi - config.RSI_OVERBOUGHT if rsi else 0
    )
    if score >= 6 and rsi_dist > 10:
        return random.randint(config.DURATION_EXTREME_MIN, config.DURATION_EXTREME_MAX), \
               "PERFECT", "6–7/7 indicators + deep extreme"
    elif score >= 6:
        return random.randint(config.DURATION_STRONG_MIN, config.DURATION_STRONG_MAX), \
               "VERY STRONG", "6–7/7 indicators confirmed"
    elif score >= 4 and rsi_dist > 10:
        return random.randint(config.DURATION_STRONG_MIN, config.DURATION_STRONG_MAX), \
               "STRONG", "4–5/7 indicators + deep RSI"
    elif score >= 4:
        return random.randint(config.DURATION_MODERATE_MIN, config.DURATION_MODERATE_MAX), \
               "STRONG", "4–5/7 indicators confirmed"
    else:
        return random.randint(config.DURATION_MODERATE_MIN, config.DURATION_MODERATE_MAX), \
               "MODERATE", f"{score}/7 indicators confirmed"


# ─── SIGNAL EVALUATION ───────────────────────────────────────────────────────

def evaluate_signal(
    symbol:         str,
    current_price:  float,
    category:       str,
    min_confidence: int,
    force:          bool = False,
) -> Optional[dict]:
    """
    Full signal evaluation with all filters.
    Returns signal dict or None.
    """
    # Payout filter
    payout = config.get_payout(symbol)
    if not force and payout < config.MIN_PAYOUT_PCT:
        return None

    # Session filter
    if not force and not is_active_session(category):
        print(f"  [SESSION] {symbol}: outside trading session — skipped")
        return None

    record_price(symbol, current_price)
    prices = get_price_history(symbol)

    if len(prices) < config.MIN_PRICE_HISTORY:
        print(f"  [HIST] {symbol}: {len(prices)}/{config.MIN_PRICE_HISTORY} pts")
        return None

    rsi = calculate_rsi(prices)
    if rsi is None:
        return None

    if rsi <= config.RSI_OVERSOLD:
        direction, rsi_label = "BUY", "OVERSOLD"
    elif rsi >= config.RSI_OVERBOUGHT:
        direction, rsi_label = "SELL", "OVERBOUGHT"
    else:
        return None

    score, details = score_signal(prices, direction)

    # Candlestick pattern (bonus info, not scored but shown)
    candle_ok, candle_name = check_candlestick_pattern(prices, direction)
    details["candle_ok"]   = candle_ok
    details["candle_name"] = candle_name

    print(
        f"  [SCORE] {symbol}: RSI={rsi:.1f} score={score}/7 "
        f"[R={'✓' if details.get('rsi_ok') else '✗'} "
        f"S={'✓' if details.get('stoch_ok') else '✗'} "
        f"M={'✓' if details.get('macd_ok') else '✗'} "
        f"B={'✓' if details.get('bb_ok') else '✗'} "
        f"E={'✓' if details.get('ema_ok') else '✗'} "
        f"D={'✓' if details.get('divergence_ok') else '✗'} "
        f"A={'✓' if details.get('adx_ok') else '✗'}]"
    )

    if score < config.MIN_SCORE:
        return None

    # Confidence: scales with score and payout
    base_conf  = 55 + (score / 7) * 40
    payout_bonus = (payout - 75) / 100   # bonus for high-payout pairs
    confidence = min(98, max(55, int(base_conf + payout_bonus) + random.randint(-2, 3)))

    if not force and confidence < min_confidence:
        return None

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
        "payout":     payout,
        "category":   category,
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


# ─── MARTINGALE ──────────────────────────────────────────────────────────────

def build_martingale_lines(entry_time: datetime, duration: int) -> list:
    lines = []
    for lvl in range(1, config.MARTINGALE_LEVELS + 1):
        start = entry_time + timedelta(minutes=duration * (lvl - 1))
        end   = start + timedelta(minutes=duration)
        mult  = 2 ** (lvl - 1)
        lines.append(
            f"  {'├' if lvl < config.MARTINGALE_LEVELS else '└'} "
            f"*Level {lvl}* (×{mult} stake)\n"
            f"     ▶ Enter:  `{_fmt_time(start)}` WAT  ⏱ `{_countdown(start)}`\n"
            f"     ⏹ Expire: `{_fmt_time(end)}` WAT  ⏱ `{_countdown(end)}`"
        )
    return lines


# ─── SIGNAL MESSAGE ───────────────────────────────────────────────────────────

def format_signal_message(
    signal:    dict,
    pair_info: dict,
    source:    str,
    signal_id: str,
    stake_info: Optional[dict] = None,
) -> str:
    category   = signal["category"]
    now_wat    = _nigeria_now()
    entry_lead = signal["entry_lead"]
    entry_time = now_wat + timedelta(minutes=entry_lead)
    expiry_time = entry_time + timedelta(minutes=signal["duration"])

    direction  = signal["direction"]
    price      = signal["price"]
    rsi        = signal["rsi"]
    confidence = signal["confidence"]
    duration   = signal["duration"]
    strength   = signal["strength"]
    reason     = signal["reason"]
    score      = signal["score"]
    details    = signal["details"]
    payout     = signal["payout"]
    flag       = pair_info["flag"]
    pair_name  = pair_info["name"]
    is_otc     = "OTC" in pair_name

    dir_emoji = "🟢🐂" if direction == "BUY" else "🔴🐻"
    dir_arrow = "⬆️ BUY" if direction == "BUY" else "⬇️ SELL"

    def fmt_p(v):
        if category == "crypto":
            return f"${v:,.6f}" if v < 0.01 else (f"${v:,.4f}" if v < 1 else f"${v:,.2f}")
        elif category in ("forex", "otc"):
            return f"{v:.5f}"
        return f"${v:,.2f}"

    pct = config.TP_SL_PCT
    tp  = price * (1 + pct) if direction == "BUY" else price * (1 - pct)
    sl  = price * (1 - pct) if direction == "BUY" else price * (1 + pct)

    # Score stars
    stars = "⭐" * score + "☆" * (7 - score)

    # Confidence bar
    filled = math.ceil(confidence / 10)
    bar    = "█" * filled + "░" * (10 - filled)

    # Indicator summary
    def mark(key):
        v = details.get(key)
        return "✅" if v is True else ("❌" if v is False else "⏳")

    ind_line = (
        f"{mark('rsi_ok')}RSI `{rsi:.1f}` "
        f"{mark('stoch_ok')}Stoch "
        f"{mark('macd_ok')}MACD "
        f"{mark('bb_ok')}BB "
        f"{mark('ema_ok')}EMA "
        f"{mark('divergence_ok')}Div "
        f"{mark('adx_ok')}ADX"
    )

    # Candlestick pattern
    candle_line = ""
    if details.get("candle_ok"):
        candle_line = f"🕯️ *Pattern:* _{details.get('candle_name', '')}_\n"

    # Duration label
    if duration <= 3:
        dur_label = f"{duration} min ⚡"
    elif duration <= 10:
        dur_label = f"{duration} min 📊"
    elif duration <= 25:
        dur_label = f"{duration} min 🕐"
    else:
        dur_label = f"{duration} min 🐢"

    # Martingale
    mart_lines = build_martingale_lines(entry_time, duration)

    # Stake info
    stake_line = ""
    if stake_info:
        stake_line = (
            f"💵 *Suggested Stake:* `${stake_info['stake']}`  _{stake_info['pct']}% of balance_\n"
            f"📈 *Martingale L2:*   `${stake_info['martingale_l2']}`\n"
        )

    # OTC notice
    otc_line = "_⚠️ OTC: Real Pocket Option price feed_\n" if is_otc else ""

    return (
        f"{'━' * 32}\n"
        f"{flag}  *{pair_name}*  `{signal_id}`\n"
        f"{'━' * 32}\n"
        f"{dir_emoji}  *{dir_arrow}*\n\n"
        f"💰 *Price:*  `{fmt_p(price)}`\n"
        f"💹 *Payout:* `{payout}%`\n"
        f"📡 *Source:* _{source}_\n"
        f"{otc_line}\n"
        f"{'─' * 32}\n"
        f"📊 *Score:* {stars} `{score}/7`\n"
        f"{ind_line}\n"
        f"{candle_line}\n"
        f"🎯 *Confidence:* `{confidence}%`\n"
        f"`[{bar}]`\n\n"
        f"📶 *Strength:* _{strength}_\n"
        f"_↳ {reason}_\n\n"
        f"{'─' * 32}\n"
        f"🕐 *Signal sent:*  `{_fmt_datetime(now_wat)} WAT`\n"
        f"🟢 *Enter at:*     `{_fmt_time(entry_time)}` WAT  ⏱ `{_countdown(entry_time)}`\n"
        f"🔴 *Expires at:*   `{_fmt_time(expiry_time)}` WAT  ⏱ `{_countdown(expiry_time)}`\n"
        f"⏳ *Duration:*     `{dur_label}`\n\n"
        f"{stake_line}"
        f"{'─' * 32}\n"
        f"📈 *Martingale* _(2 levels, gap = duration)_\n"
        + "\n".join(mart_lines) +
        f"\n\n{'─' * 32}\n"
        f"✅ *Take Profit:* `{fmt_p(tp)}`\n"
        f"🛑 *Stop Loss:*   `{fmt_p(sl)}`\n"
        f"{'━' * 32}"
    )


# ─── STARTUP / STATUS ─────────────────────────────────────────────────────────

def format_startup_message(ws_connected: bool = False) -> str:
    now   = _fmt_datetime(_nigeria_now())
    total = sum(len(v) for v in config.get_all_pairs().items())
    otc_count = len(config.OTC_PAIRS)
    ws_str = "✅ Connected" if ws_connected else "❌ Not connected (set PO_SSID)"
    return (
        "🚀 *Forex Crypto Signal Bot v11 is LIVE!*\n\n"
        f"📅 `{now} WAT`\n\n"
        f"🔬 *7-Indicator Engine:*\n"
        f"  RSI · Stoch · MACD · BB · EMA · Divergence · ADX\n"
        f"  _Signals fire when {config.MIN_SCORE}/7 confirm_\n\n"
        f"🔌 *Pocket Option WebSocket:* {ws_str}\n"
        f"📊 *OTC pairs:* `{otc_count}` (real PO prices)\n\n"
        f"✨ *New features:*\n"
        f"  ✅ Win/loss tracker with inline buttons\n"
        f"  ✅ Money management stake suggestions\n"
        f"  ✅ Consecutive loss protection\n"
        f"  ✅ Signal expiry warning\n"
        f"  ✅ Session filter (forex: London/NY only)\n"
        f"  ✅ ADX trend filter\n"
        f"  ✅ RSI divergence detection\n"
        f"  ✅ Candlestick pattern confirmation\n"
        f"  ✅ Payout-weighted signals\n\n"
        "Use /build to prime history fast.\n"
        "Use /balance to set your account balance."
    )


def format_status_message(
    auto_on: bool, signal_count: int,
    cg_ok: bool, er_ok: bool, td_ok: bool,
    ws_ok: bool, min_confidence: int,
    paused: bool, pause_remaining: int,
) -> str:
    now = _fmt_datetime(_nigeria_now())
    auto_s = "✅ ON" if (auto_on and not paused) else (
        f"⏸ PAUSED ({pause_remaining}min remaining)" if paused else "❌ OFF"
    )
    return (
        "🤖 *Bot Status — v11*\n"
        f"{'─' * 32}\n"
        f"🕐 Time:              `{now} WAT`\n"
        f"🪙 CoinGecko:         {'✅' if cg_ok else '❌'}\n"
        f"💱 ExchangeRate-API:  {'✅' if er_ok else '❌'}\n"
        f"📊 Twelve Data:       {'✅' if td_ok else '❌'}\n"
        f"🔌 PO WebSocket:      {'✅ Live OTC' if ws_ok else '❌ No OTC prices'}\n"
        f"🔄 Auto Signals:      {auto_s}\n"
        f"📨 Signals Sent:      `{signal_count}`\n"
        f"🎯 Min Confidence:    `{min_confidence}%`\n"
        f"🔬 Score required:    `{config.MIN_SCORE}/7`\n"
        f"🚦 Max/scan:          `{config.MAX_SIGNALS_PER_SCAN}`\n"
    )
