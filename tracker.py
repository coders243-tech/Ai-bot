# tracker.py  –  v11
# Tracks every signal result, win/loss rate, consecutive losses,
# signal expiry, and money management stake suggestions.

import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import config

# ─── ACTIVE SIGNALS ──────────────────────────────────────────────────────────
# Signals that have been sent but not yet expired.
# { signal_id: signal_dict }
_active_signals: dict[str, dict] = {}

# ─── RESULT HISTORY ──────────────────────────────────────────────────────────
# Rolling store of completed signal results.
# Each entry: { symbol, direction, entry_price, result, timestamp, duration, payout }
_signal_results: deque = deque(maxlen=500)

# ─── CONSECUTIVE LOSS TRACKER ────────────────────────────────────────────────
_consecutive_losses: int  = 0
_paused_until:       float = 0   # unix timestamp — auto signals paused until this time

# ─── SIGNAL ID COUNTER ───────────────────────────────────────────────────────
_signal_counter: int = 0


def _nigeria_now() -> datetime:
    return datetime.now(tz=timezone(timedelta(hours=config.TIMEZONE_OFFSET)))


# ─── REGISTER A NEW SIGNAL ───────────────────────────────────────────────────

def register_signal(signal: dict, entry_time: datetime, expiry_time: datetime) -> str:
    """
    Register a newly sent signal for tracking.
    Returns the signal ID string (e.g. "#042").
    """
    global _signal_counter
    _signal_counter += 1
    sid = f"#{_signal_counter:03d}"

    _active_signals[sid] = {
        "id":          sid,
        "symbol":      signal["symbol"],
        "direction":   signal["direction"],
        "entry_price": signal["price"],
        "entry_time":  entry_time,
        "expiry_time": expiry_time,
        "duration":    signal["duration"],
        "confidence":  signal["confidence"],
        "score":       signal.get("score", 0),
        "notified_expiry": False,
    }
    return sid


def get_active_signals() -> list:
    return list(_active_signals.values())


# ─── SIGNAL EXPIRY CHECK ─────────────────────────────────────────────────────

def check_expired_signals() -> list:
    """
    Check all active signals for expiry.
    Returns list of signals that just expired (entry window passed).
    Removes them from active tracking.
    """
    now    = _nigeria_now()
    expired = []
    to_remove = []

    for sid, sig in _active_signals.items():
        entry_time = sig["entry_time"]
        if now >= entry_time and not sig.get("notified_expiry"):
            # Entry window has passed — if not entered, signal is stale
            expired.append(sig)
            sig["notified_expiry"] = True

        # Remove signals that are well past expiry (30 min buffer)
        expiry_time = sig["expiry_time"]
        if now > expiry_time + timedelta(minutes=30):
            to_remove.append(sid)

    for sid in to_remove:
        _active_signals.pop(sid, None)

    return expired


# ─── RECORD RESULT (from inline button tap) ──────────────────────────────────

def record_result(sid: str, result: str) -> Optional[dict]:
    """
    Record WIN or LOSS for a signal.
    result: "WIN" or "LOSS"
    Returns summary dict or None if signal not found.
    """
    global _consecutive_losses

    sig = _active_signals.get(sid)
    if sig is None:
        # Try to find by recent signals even if already cleaned up
        return None

    payout = config.get_payout(sig["symbol"])
    entry  = {
        "signal_id":   sid,
        "symbol":      sig["symbol"],
        "direction":   sig["direction"],
        "result":      result,
        "timestamp":   time.time(),
        "duration":    sig["duration"],
        "confidence":  sig["confidence"],
        "score":       sig.get("score", 0),
        "payout":      payout,
    }
    _signal_results.append(entry)
    _active_signals.pop(sid, None)

    # Update consecutive loss counter
    if result == "WIN":
        _consecutive_losses = 0
    else:
        _consecutive_losses += 1
        if _consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
            _paused_until = time.time() + config.LOSS_PAUSE_MINUTES * 60
            print(f"[Tracker] {_consecutive_losses} consecutive losses — "
                  f"auto signals paused for {config.LOSS_PAUSE_MINUTES} min")

    return entry


# ─── PAUSE STATE ─────────────────────────────────────────────────────────────

def is_paused() -> bool:
    """Return True if auto signals are currently paused due to losses."""
    return time.time() < _paused_until


def pause_remaining_minutes() -> int:
    remaining = _paused_until - time.time()
    return max(0, int(remaining / 60))


def resume_manually() -> None:
    """Manually resume signals (overrides the pause timer)."""
    global _paused_until, _consecutive_losses
    _paused_until = 0
    _consecutive_losses = 0


# ─── STATISTICS ──────────────────────────────────────────────────────────────

def get_statistics() -> dict:
    """Return comprehensive win/loss statistics."""
    results = list(_signal_results)
    if not results:
        return {
            "total": 0, "wins": 0, "losses": 0,
            "win_rate": 0.0, "profit_factor": 0.0,
            "by_symbol": {}, "by_confidence": {},
            "consecutive_losses": _consecutive_losses,
        }

    wins   = [r for r in results if r["result"] == "WIN"]
    losses = [r for r in results if r["result"] == "LOSS"]
    total  = len(results)
    win_rate = (len(wins) / total * 100) if total > 0 else 0

    # Profit factor (simplified — assumes fixed stake)
    avg_payout = sum(r["payout"] for r in wins) / len(wins) if wins else 0
    profit_factor = (len(wins) * avg_payout / 100) / len(losses) if losses else float("inf")

    # By symbol
    by_symbol: dict = {}
    for r in results:
        sym = r["symbol"]
        if sym not in by_symbol:
            by_symbol[sym] = {"wins": 0, "losses": 0}
        by_symbol[sym]["wins"   if r["result"] == "WIN" else "losses"] += 1

    # By confidence bracket
    by_conf: dict = {}
    for r in results:
        bracket = f"{(r['confidence'] // 10) * 10}–{(r['confidence'] // 10) * 10 + 9}%"
        if bracket not in by_conf:
            by_conf[bracket] = {"wins": 0, "losses": 0}
        by_conf[bracket]["wins" if r["result"] == "WIN" else "losses"] += 1

    return {
        "total":               total,
        "wins":                len(wins),
        "losses":              len(losses),
        "win_rate":            round(win_rate, 1),
        "profit_factor":       round(profit_factor, 2),
        "by_symbol":           by_symbol,
        "by_confidence":       by_conf,
        "consecutive_losses":  _consecutive_losses,
    }


def get_best_pairs(min_trades: int = 5) -> list:
    """Return pairs sorted by win rate (min_trades threshold)."""
    stats = get_statistics()
    pairs = []
    for sym, data in stats["by_symbol"].items():
        total = data["wins"] + data["losses"]
        if total >= min_trades:
            wr = data["wins"] / total * 100
            pairs.append((sym, round(wr, 1), total))
    return sorted(pairs, key=lambda x: x[1], reverse=True)


def get_worst_pairs(min_trades: int = 5) -> list:
    """Return pairs with lowest win rate."""
    return list(reversed(get_best_pairs(min_trades)))


# ─── MONEY MANAGEMENT ────────────────────────────────────────────────────────

def suggest_stake(confidence: int, balance: float) -> dict:
    """
    Suggest stake size based on confidence score and account balance.
    Uses fractional Kelly criterion scaled conservatively.

    Returns { stake, pct, martingale_l2 }
    """
    if confidence >= 85:
        pct = 3.0   # 3% of balance
    elif confidence >= 70:
        pct = 2.0   # 2% of balance
    else:
        pct = 1.0   # 1% of balance — low confidence

    # Cap at 5% regardless of confidence
    pct   = min(pct, 5.0)
    stake = round(balance * pct / 100, 2)

    # Martingale Level 2 = 2× stake
    return {
        "stake":          stake,
        "pct":            pct,
        "martingale_l2":  round(stake * 2, 2),
        "total_exposure": round(stake * 3, 2),   # L1 + L2 combined
    }


# ─── DAILY SUMMARY ───────────────────────────────────────────────────────────

def daily_summary() -> str:
    """Format a daily performance summary for Telegram."""
    stats = get_statistics()
    if stats["total"] == 0:
        return "📊 *Daily Summary*\n_No trades recorded today._"

    # Best pair
    best = get_best_pairs(3)
    best_str = f"`{best[0][0]}` ({best[0][1]}%)" if best else "_N/A_"

    # Worst pair
    worst = get_worst_pairs(3)
    worst_str = f"`{worst[0][0]}` ({worst[0][1]}%)" if worst else "_N/A_"

    bar_filled = int(stats["win_rate"] / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    return (
        "📊 *Daily Performance Summary*\n"
        f"{'─' * 32}\n"
        f"📨 Total signals:   `{stats['total']}`\n"
        f"✅ Wins:            `{stats['wins']}`\n"
        f"❌ Losses:          `{stats['losses']}`\n"
        f"🎯 Win Rate:        `{stats['win_rate']}%`\n"
        f"`[{bar}]`\n"
        f"💰 Profit Factor:   `{stats['profit_factor']}`\n"
        f"🏆 Best pair:       {best_str}\n"
        f"⚠️ Worst pair:     {worst_str}\n"
        f"{'─' * 32}\n"
        f"_Record results with ✅/❌ buttons on each signal._"
    )
