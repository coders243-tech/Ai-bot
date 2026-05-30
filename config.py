# config.py  –  Forex Crypto Signal Bot v11
# Complete configuration: indicators, pairs, payout table, all filters.

# ─── TIMEZONE ────────────────────────────────────────────────────────────────
TIMEZONE_NAME   = "WAT"
TIMEZONE_OFFSET = 1   # UTC+1 Nigeria

# ─── RSI ─────────────────────────────────────────────────────────────────────
RSI_PERIOD       = 7
RSI_OVERSOLD     = 30
RSI_OVERBOUGHT   = 70

# ─── EMA ─────────────────────────────────────────────────────────────────────
EMA_FAST         = 5
EMA_SLOW         = 10

# ─── MACD ────────────────────────────────────────────────────────────────────
MACD_FAST        = 6
MACD_SLOW        = 12
MACD_SIGNAL      = 5

# ─── STOCHASTIC ──────────────────────────────────────────────────────────────
STOCH_K_PERIOD   = 7
STOCH_D_PERIOD   = 3
STOCH_OVERSOLD   = 20
STOCH_OVERBOUGHT = 80

# ─── BOLLINGER BANDS ─────────────────────────────────────────────────────────
BB_PERIOD        = 10
BB_STD_DEV       = 2.0

# ─── ADX (Average Directional Index — trend strength filter) ─────────────────
# When ADX > ADX_THRESHOLD the market is strongly trending.
# Indicators fail in strong trends — we skip signals when ADX is high.
ADX_PERIOD       = 7
ADX_THRESHOLD    = 25

# ─── SIGNAL SCORING ──────────────────────────────────────────────────────────
# 7 possible confirmations:
#   RSI, Stochastic, MACD, Bollinger Bands, EMA, Divergence, ADX (ranging)
MIN_PRICE_HISTORY = 20
MIN_SCORE         = 3   # 3/7 minimum to fire a signal

# ─── SCAN SETTINGS ───────────────────────────────────────────────────────────
SCAN_INTERVAL_MIN    = 10
SCAN_INTERVAL_MAX    = 12
COOLDOWN_SECONDS     = 600
CONFIDENCE_DEFAULT   = 50
MAX_SIGNALS_PER_SCAN = 5

# ─── MARTINGALE ──────────────────────────────────────────────────────────────
MARTINGALE_LEVELS         = 2
MARTINGALE_GAP_MULTIPLIER = 1

# ─── TP / SL ─────────────────────────────────────────────────────────────────
TP_SL_PCT        = 0.005

# ─── ENTRY LEAD TIME ─────────────────────────────────────────────────────────
ENTRY_LEAD_MIN   = 1
ENTRY_LEAD_MAX   = 5

# ─── DYNAMIC DURATION ────────────────────────────────────────────────────────
DURATION_EXTREME_MIN  = 1
DURATION_EXTREME_MAX  = 3
DURATION_STRONG_MIN   = 4
DURATION_STRONG_MAX   = 10
DURATION_MODERATE_MIN = 11
DURATION_MODERATE_MAX = 25
DURATION_MILD_MIN     = 26
DURATION_MILD_MAX     = 60

# ─── CONSECUTIVE LOSS PROTECTION ────────────────────────────────────────────
MAX_CONSECUTIVE_LOSSES = 3
LOSS_PAUSE_MINUTES     = 30

# ─── TRADING SESSION FILTER (UTC hours) ─────────────────────────────────────
# Forex signals only during London + New York sessions.
# Crypto has no session filter.
SESSION_START = 8    # 08:00 UTC (London open)
SESSION_END   = 21   # 21:00 UTC (New York close)

# ─── MINIMUM PAYOUT ──────────────────────────────────────────────────────────
MIN_PAYOUT_PCT = 75

# ─── POCKET OPTION OTC ASSET IDs ────────────────────────────────────────────
# Internal Pocket Option WebSocket asset IDs for OTC pairs.
PO_OTC_ASSET_IDS = {
    "EURUSD_OTC": 1,   "GBPUSD_OTC": 2,   "USDJPY_OTC": 3,
    "USDCHF_OTC": 4,   "AUDUSD_OTC": 5,   "USDCAD_OTC": 6,
    "NZDUSD_OTC": 7,   "EURGBP_OTC": 8,   "EURJPY_OTC": 9,
    "GBPJPY_OTC": 10,  "AUDJPY_OTC": 11,  "CADJPY_OTC": 14,
    "CHFJPY_OTC": 15,  "EURCHF_OTC": 16,  "GBPAUD_OTC": 17,
    "GBPCAD_OTC": 18,  "GBPCHF_OTC": 19,  "EURCAD_OTC": 20,
    "EURAUD_OTC": 21,  "AUDCAD_OTC": 22,  "AUDNZD_OTC": 23,
    "AUDCHF_OTC": 24,  "NZDJPY_OTC": 25,  "CADCHF_OTC": 26,
    "BTCUSD_OTC": 100, "ETHUSD_OTC": 101,
    "LTCUSD_OTC": 102, "DOGEUSD_OTC": 103,
}

# ─── PAYOUT TABLE ────────────────────────────────────────────────────────────
PAYOUT_TABLE = {
    "EURUSD_OTC": 92,  "GBPUSD_OTC": 92,  "USDJPY_OTC": 92,
    "USDCHF_OTC": 92,  "AUDUSD_OTC": 92,  "USDCAD_OTC": 92,
    "NZDUSD_OTC": 92,  "EURGBP_OTC": 92,  "EURJPY_OTC": 92,
    "GBPJPY_OTC": 92,  "AUDJPY_OTC": 92,  "CADJPY_OTC": 92,
    "CHFJPY_OTC": 92,  "EURCHF_OTC": 92,  "GBPAUD_OTC": 92,
    "GBPCAD_OTC": 92,  "GBPCHF_OTC": 92,  "EURCAD_OTC": 92,
    "EURAUD_OTC": 92,  "AUDCAD_OTC": 92,  "AUDNZD_OTC": 92,
    "AUDCHF_OTC": 92,  "NZDJPY_OTC": 92,  "CADCHF_OTC": 92,
    "BTCUSD_OTC": 92,  "ETHUSD_OTC": 92,
    "LTCUSD_OTC": 91,  "DOGEUSD_OTC": 91,
    "EURUSD": 80,  "GBPUSD": 80,  "USDJPY": 80,
    "USDCHF": 78,  "AUDUSD": 78,  "USDCAD": 78,
    "NZDUSD": 76,  "EURGBP": 76,  "EURJPY": 76,
    "GBPJPY": 75,  "AUDJPY": 75,  "GBPAUD": 75,
    "EURCAD": 75,  "GBPCAD": 75,  "CADJPY": 75,
    "CHFJPY": 75,  "AUDCAD": 75,  "GBPCHF": 75,
    "EURCHF": 75,  "AUDNZD": 75,
    "BTCUSDT": 85, "ETHUSDT": 85, "BNBUSDT": 82,
    "SOLUSDT": 82, "XRPUSDT": 80, "ADAUSDT": 78,
    "DOGEUSDT": 78, "LTCUSDT": 78, "TRXUSDT": 76,
    "DOTUSDT": 76,  "AVAXUSDT": 76, "LINKUSDT": 76,
    "AAPL": 92,  "MSFT": 92,  "TSLA": 87,
    "NVDA": 92,  "META": 92,  "NFLX": 92,
    "INTC": 92,  "COIN": 78,  "PLTR": 92, "GME": 75,
    "SPX": 53,   "NDX": 53,   "DJI": 53,
    "FTSE": 53,  "DAX": 53,
    "XAU/USD": 88, "XAG/USD": 88,
    "WTI/USD": 88, "BRENT/USD": 88,
}

def get_payout(symbol: str) -> int:
    return PAYOUT_TABLE.get(symbol, 75)

# ─── PAIRS ───────────────────────────────────────────────────────────────────

CRYPTO_PAIRS = {
    "BTCUSDT":  {"name": "Bitcoin/USD",   "flag": "🟡", "cg_id": "bitcoin"},
    "ETHUSDT":  {"name": "Ethereum/USD",  "flag": "🔷", "cg_id": "ethereum"},
    "BNBUSDT":  {"name": "BNB/USD",       "flag": "🟨", "cg_id": "binancecoin"},
    "SOLUSDT":  {"name": "Solana/USD",    "flag": "🟣", "cg_id": "solana"},
    "XRPUSDT":  {"name": "XRP/USD",       "flag": "🔵", "cg_id": "ripple"},
    "ADAUSDT":  {"name": "Cardano/USD",   "flag": "💙", "cg_id": "cardano"},
    "DOGEUSDT": {"name": "Dogecoin/USD",  "flag": "🐶", "cg_id": "dogecoin"},
    "LTCUSDT":  {"name": "Litecoin/USD",  "flag": "⚪", "cg_id": "litecoin"},
    "TRXUSDT":  {"name": "TRON/USD",      "flag": "🔴", "cg_id": "tron"},
    "DOTUSDT":  {"name": "Polkadot/USD",  "flag": "⚫", "cg_id": "polkadot"},
    "AVAXUSDT": {"name": "Avalanche/USD", "flag": "🔺", "cg_id": "avalanche-2"},
    "LINKUSDT": {"name": "Chainlink/USD", "flag": "🔗", "cg_id": "chainlink"},
}

FOREX_PAIRS = {
    "EURUSD": {"name": "EUR/USD", "flag": "🇪🇺🇺🇸"},
    "GBPUSD": {"name": "GBP/USD", "flag": "🇬🇧🇺🇸"},
    "USDJPY": {"name": "USD/JPY", "flag": "🇺🇸🇯🇵"},
    "USDCHF": {"name": "USD/CHF", "flag": "🇺🇸🇨🇭"},
    "AUDUSD": {"name": "AUD/USD", "flag": "🇦🇺🇺🇸"},
    "USDCAD": {"name": "USD/CAD", "flag": "🇺🇸🇨🇦"},
    "NZDUSD": {"name": "NZD/USD", "flag": "🇳🇿🇺🇸"},
    "EURGBP": {"name": "EUR/GBP", "flag": "🇪🇺🇬🇧"},
    "EURJPY": {"name": "EUR/JPY", "flag": "🇪🇺🇯🇵"},
    "GBPJPY": {"name": "GBP/JPY", "flag": "🇬🇧🇯🇵"},
    "AUDJPY": {"name": "AUD/JPY", "flag": "🇦🇺🇯🇵"},
    "GBPAUD": {"name": "GBP/AUD", "flag": "🇬🇧🇦🇺"},
    "EURCAD": {"name": "EUR/CAD", "flag": "🇪🇺🇨🇦"},
    "GBPCAD": {"name": "GBP/CAD", "flag": "🇬🇧🇨🇦"},
    "CADJPY": {"name": "CAD/JPY", "flag": "🇨🇦🇯🇵"},
    "CHFJPY": {"name": "CHF/JPY", "flag": "🇨🇭🇯🇵"},
    "AUDCAD": {"name": "AUD/CAD", "flag": "🇦🇺🇨🇦"},
    "GBPCHF": {"name": "GBP/CHF", "flag": "🇬🇧🇨🇭"},
    "EURCHF": {"name": "EUR/CHF", "flag": "🇪🇺🇨🇭"},
    "AUDNZD": {"name": "AUD/NZD", "flag": "🇦🇺🇳🇿"},
}

OTC_PAIRS = {
    "EURUSD_OTC":  {"name": "EUR/USD OTC",  "flag": "🇪🇺🇺🇸"},
    "GBPUSD_OTC":  {"name": "GBP/USD OTC",  "flag": "🇬🇧🇺🇸"},
    "USDJPY_OTC":  {"name": "USD/JPY OTC",  "flag": "🇺🇸🇯🇵"},
    "USDCHF_OTC":  {"name": "USD/CHF OTC",  "flag": "🇺🇸🇨🇭"},
    "AUDUSD_OTC":  {"name": "AUD/USD OTC",  "flag": "🇦🇺🇺🇸"},
    "USDCAD_OTC":  {"name": "USD/CAD OTC",  "flag": "🇺🇸🇨🇦"},
    "NZDUSD_OTC":  {"name": "NZD/USD OTC",  "flag": "🇳🇿🇺🇸"},
    "EURGBP_OTC":  {"name": "EUR/GBP OTC",  "flag": "🇪🇺🇬🇧"},
    "EURJPY_OTC":  {"name": "EUR/JPY OTC",  "flag": "🇪🇺🇯🇵"},
    "GBPJPY_OTC":  {"name": "GBP/JPY OTC",  "flag": "🇬🇧🇯🇵"},
    "AUDJPY_OTC":  {"name": "AUD/JPY OTC",  "flag": "🇦🇺🇯🇵"},
    "CADJPY_OTC":  {"name": "CAD/JPY OTC",  "flag": "🇨🇦🇯🇵"},
    "CHFJPY_OTC":  {"name": "CHF/JPY OTC",  "flag": "🇨🇭🇯🇵"},
    "EURCHF_OTC":  {"name": "EUR/CHF OTC",  "flag": "🇪🇺🇨🇭"},
    "GBPAUD_OTC":  {"name": "GBP/AUD OTC",  "flag": "🇬🇧🇦🇺"},
    "GBPCAD_OTC":  {"name": "GBP/CAD OTC",  "flag": "🇬🇧🇨🇦"},
    "GBPCHF_OTC":  {"name": "GBP/CHF OTC",  "flag": "🇬🇧🇨🇭"},
    "EURCAD_OTC":  {"name": "EUR/CAD OTC",  "flag": "🇪🇺🇨🇦"},
    "EURAUD_OTC":  {"name": "EUR/AUD OTC",  "flag": "🇪🇺🇦🇺"},
    "AUDCAD_OTC":  {"name": "AUD/CAD OTC",  "flag": "🇦🇺🇨🇦"},
    "AUDNZD_OTC":  {"name": "AUD/NZD OTC",  "flag": "🇦🇺🇳🇿"},
    "AUDCHF_OTC":  {"name": "AUD/CHF OTC",  "flag": "🇦🇺🇨🇭"},
    "NZDJPY_OTC":  {"name": "NZD/JPY OTC",  "flag": "🇳🇿🇯🇵"},
    "CADCHF_OTC":  {"name": "CAD/CHF OTC",  "flag": "🇨🇦🇨🇭"},
    "BTCUSD_OTC":  {"name": "Bitcoin OTC",  "flag": "🟡"},
    "ETHUSD_OTC":  {"name": "Ethereum OTC", "flag": "🔷"},
    "LTCUSD_OTC":  {"name": "Litecoin OTC", "flag": "⚪"},
    "DOGEUSD_OTC": {"name": "Dogecoin OTC", "flag": "🐶"},
}

INDICES_PAIRS = {
    "SPX":  {"name": "S&P 500",    "flag": "🇺🇸📈"},
    "NDX":  {"name": "NASDAQ-100", "flag": "🇺🇸💻"},
    "DJI":  {"name": "Dow Jones",  "flag": "🇺🇸🏭"},
    "FTSE": {"name": "FTSE 100",   "flag": "🇬🇧📊"},
    "DAX":  {"name": "DAX 30",     "flag": "🇩🇪📊"},
}

COMMODITIES_PAIRS = {
    "XAU/USD":   {"name": "Gold",        "flag": "🥇"},
    "XAG/USD":   {"name": "Silver",      "flag": "🥈"},
    "WTI/USD":   {"name": "WTI Crude",   "flag": "🛢️"},
    "BRENT/USD": {"name": "Brent Crude", "flag": "🛢️"},
}

STOCKS_PAIRS = {
    "AAPL": {"name": "Apple",     "flag": "🍎"},
    "MSFT": {"name": "Microsoft", "flag": "🪟"},
    "TSLA": {"name": "Tesla",     "flag": "⚡"},
    "NVDA": {"name": "NVIDIA",    "flag": "🟩"},
    "META": {"name": "Meta",      "flag": "📘"},
    "NFLX": {"name": "Netflix",   "flag": "🎬"},
    "INTC": {"name": "Intel",     "flag": "🔲"},
    "COIN": {"name": "Coinbase",  "flag": "🪙"},
    "PLTR": {"name": "Palantir",  "flag": "🔭"},
    "GME":  {"name": "GameStop",  "flag": "🎮"},
}

def get_all_pairs() -> dict:
    return {
        "crypto":      CRYPTO_PAIRS,
        "forex":       FOREX_PAIRS,
        "otc":         OTC_PAIRS,
        "indices":     INDICES_PAIRS,
        "commodities": COMMODITIES_PAIRS,
        "stocks":      STOCKS_PAIRS,
    }

def find_pair(symbol: str):
    sym = symbol.upper()
    for category, pairs in get_all_pairs().items():
        if sym in pairs:
            return category, sym, pairs[sym]
    return None, None, None

def all_symbols_flat() -> list:
    return [(cat, sym) for cat, pairs in get_all_pairs().items() for sym in pairs]
