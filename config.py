# config.py  –  Forex Crypto Signal Bot v10
# OTC pairs removed — real market pairs only.

# ─── RSI SETTINGS ────────────────────────────────────────────────────────────
RSI_PERIOD       = 7
RSI_OVERSOLD     = 30
RSI_OVERBOUGHT   = 70

# ─── INDICATOR SETTINGS ──────────────────────────────────────────────────────
EMA_FAST          = 5
EMA_SLOW          = 10
MACD_FAST         = 6
MACD_SLOW         = 12
MACD_SIGNAL       = 5
STOCH_K_PERIOD    = 7
STOCH_D_PERIOD    = 3
STOCH_OVERSOLD    = 20
STOCH_OVERBOUGHT  = 80
BB_PERIOD         = 10
BB_STD_DEV        = 2.0
MIN_PRICE_HISTORY = 20   # ~3.5 hrs at 10-min scans
MIN_SCORE         = 3    # 3 out of 5 indicators must confirm

# ─── SCAN SETTINGS ───────────────────────────────────────────────────────────
SCAN_INTERVAL_MIN    = 10
SCAN_INTERVAL_MAX    = 12
COOLDOWN_SECONDS     = 600   # 10 min cooldown per pair (1 scan cycle)
CONFIDENCE_DEFAULT   = 50
MARTINGALE_LEVELS    = 2
MARTINGALE_GAP_MULTIPLIER = 1
TP_SL_PCT            = 0.005
MAX_SIGNALS_PER_SCAN = 5    # raised from 3 — more signals per scan

# ─── DYNAMIC DURATION ────────────────────────────────────────────────────────
DURATION_EXTREME_MIN  = 1
DURATION_EXTREME_MAX  = 3
DURATION_STRONG_MIN   = 4
DURATION_STRONG_MAX   = 10
DURATION_MODERATE_MIN = 11
DURATION_MODERATE_MAX = 25
DURATION_MILD_MIN     = 26
DURATION_MILD_MAX     = 60

# ─── ENTRY LEAD TIME ─────────────────────────────────────────────────────────
ENTRY_LEAD_MIN = 1
ENTRY_LEAD_MAX = 5

# ─── TIMEZONE ────────────────────────────────────────────────────────────────
TIMEZONE_NAME   = "WAT"
TIMEZONE_OFFSET = 1

# ─── CRYPTO PAIRS  (CoinGecko) ───────────────────────────────────────────────
CRYPTO_PAIRS = {
    "BTCUSDT":   {"name": "Bitcoin/USDT",    "flag": "🟡", "cg_id": "bitcoin"},
    "ETHUSDT":   {"name": "Ethereum/USDT",   "flag": "🔷", "cg_id": "ethereum"},
    "BNBUSDT":   {"name": "BNB/USDT",        "flag": "🟨", "cg_id": "binancecoin"},
    "SOLUSDT":   {"name": "Solana/USDT",     "flag": "🟣", "cg_id": "solana"},
    "XRPUSDT":   {"name": "XRP/USDT",        "flag": "🔵", "cg_id": "ripple"},
    "ADAUSDT":   {"name": "Cardano/USDT",    "flag": "💙", "cg_id": "cardano"},
    "DOGEUSDT":  {"name": "Dogecoin/USDT",   "flag": "🐶", "cg_id": "dogecoin"},
    "AVAXUSDT":  {"name": "Avalanche/USDT",  "flag": "🔺", "cg_id": "avalanche-2"},
    "DOTUSDT":   {"name": "Polkadot/USDT",   "flag": "⚫", "cg_id": "polkadot"},
    "MATICUSDT": {"name": "Polygon/USDT",    "flag": "🟪", "cg_id": "matic-network"},
    "LTCUSDT":   {"name": "Litecoin/USDT",   "flag": "⚪", "cg_id": "litecoin"},
    "TRXUSDT":   {"name": "TRON/USDT",       "flag": "🔴", "cg_id": "tron"},
    "TONUSDT":   {"name": "Toncoin/USDT",    "flag": "💎", "cg_id": "the-open-network"},
    "LINKUSDT":  {"name": "Chainlink/USDT",  "flag": "🔗", "cg_id": "chainlink"},
    "UNIUSDT":   {"name": "Uniswap/USDT",    "flag": "🦄", "cg_id": "uniswap"},
    "ATOMUSDT":  {"name": "Cosmos/USDT",     "flag": "⚛️", "cg_id": "cosmos"},
    "NEARUSDT":  {"name": "NEAR/USDT",       "flag": "🌐", "cg_id": "near"},
    "XLMUSDT":   {"name": "Stellar/USDT",    "flag": "✨", "cg_id": "stellar"},
    "ETCUSDT":   {"name": "Ethereum Classic","flag": "🟩", "cg_id": "ethereum-classic"},
    "FILUSDT":   {"name": "Filecoin/USDT",   "flag": "📁", "cg_id": "filecoin"},
}

# ─── FOREX PAIRS  (open.er-api.com — free, no key) ───────────────────────────
FOREX_PAIRS = {
    # Majors
    "EURUSD": {"name": "EUR/USD", "flag": "🇪🇺🇺🇸", "base": "EUR", "quote": "USD"},
    "GBPUSD": {"name": "GBP/USD", "flag": "🇬🇧🇺🇸", "base": "GBP", "quote": "USD"},
    "USDJPY": {"name": "USD/JPY", "flag": "🇺🇸🇯🇵", "base": "USD", "quote": "JPY"},
    "USDCHF": {"name": "USD/CHF", "flag": "🇺🇸🇨🇭", "base": "USD", "quote": "CHF"},
    "AUDUSD": {"name": "AUD/USD", "flag": "🇦🇺🇺🇸", "base": "AUD", "quote": "USD"},
    "USDCAD": {"name": "USD/CAD", "flag": "🇺🇸🇨🇦", "base": "USD", "quote": "CAD"},
    "NZDUSD": {"name": "NZD/USD", "flag": "🇳🇿🇺🇸", "base": "NZD", "quote": "USD"},
    # EUR crosses
    "EURGBP": {"name": "EUR/GBP", "flag": "🇪🇺🇬🇧", "base": "EUR", "quote": "GBP"},
    "EURJPY": {"name": "EUR/JPY", "flag": "🇪🇺🇯🇵", "base": "EUR", "quote": "JPY"},
    "EURCHF": {"name": "EUR/CHF", "flag": "🇪🇺🇨🇭", "base": "EUR", "quote": "CHF"},
    "EURCAD": {"name": "EUR/CAD", "flag": "🇪🇺🇨🇦", "base": "EUR", "quote": "CAD"},
    "EURAUD": {"name": "EUR/AUD", "flag": "🇪🇺🇦🇺", "base": "EUR", "quote": "AUD"},
    "EURNZD": {"name": "EUR/NZD", "flag": "🇪🇺🇳🇿", "base": "EUR", "quote": "NZD"},
    "EURTRY": {"name": "EUR/TRY", "flag": "🇪🇺🇹🇷", "base": "EUR", "quote": "TRY"},
    # GBP crosses
    "GBPJPY": {"name": "GBP/JPY", "flag": "🇬🇧🇯🇵", "base": "GBP", "quote": "JPY"},
    "GBPAUD": {"name": "GBP/AUD", "flag": "🇬🇧🇦🇺", "base": "GBP", "quote": "AUD"},
    "GBPCAD": {"name": "GBP/CAD", "flag": "🇬🇧🇨🇦", "base": "GBP", "quote": "CAD"},
    "GBPCHF": {"name": "GBP/CHF", "flag": "🇬🇧🇨🇭", "base": "GBP", "quote": "CHF"},
    "GBPNZD": {"name": "GBP/NZD", "flag": "🇬🇧🇳🇿", "base": "GBP", "quote": "NZD"},
    # AUD crosses
    "AUDJPY": {"name": "AUD/JPY", "flag": "🇦🇺🇯🇵", "base": "AUD", "quote": "JPY"},
    "AUDCAD": {"name": "AUD/CAD", "flag": "🇦🇺🇨🇦", "base": "AUD", "quote": "CAD"},
    "AUDNZD": {"name": "AUD/NZD", "flag": "🇦🇺🇳🇿", "base": "AUD", "quote": "NZD"},
    "AUDCHF": {"name": "AUD/CHF", "flag": "🇦🇺🇨🇭", "base": "AUD", "quote": "CHF"},
    # CAD / CHF / NZD crosses
    "CADJPY": {"name": "CAD/JPY", "flag": "🇨🇦🇯🇵", "base": "CAD", "quote": "JPY"},
    "CADCHF": {"name": "CAD/CHF", "flag": "🇨🇦🇨🇭", "base": "CAD", "quote": "CHF"},
    "CHFJPY": {"name": "CHF/JPY", "flag": "🇨🇭🇯🇵", "base": "CHF", "quote": "JPY"},
    "NZDJPY": {"name": "NZD/JPY", "flag": "🇳🇿🇯🇵", "base": "NZD", "quote": "JPY"},
    # African & emerging
    "USDNGN": {"name": "USD/NGN", "flag": "🇺🇸🇳🇬", "base": "USD", "quote": "NGN"},
    "USDKES": {"name": "USD/KES", "flag": "🇺🇸🇰🇪", "base": "USD", "quote": "KES"},
    "USDZAR": {"name": "USD/ZAR", "flag": "🇺🇸🇿🇦", "base": "USD", "quote": "ZAR"},
    "USDINR": {"name": "USD/INR", "flag": "🇺🇸🇮🇳", "base": "USD", "quote": "INR"},
    "USDSGD": {"name": "USD/SGD", "flag": "🇺🇸🇸🇬", "base": "USD", "quote": "SGD"},
    "USDMXN": {"name": "USD/MXN", "flag": "🇺🇸🇲🇽", "base": "USD", "quote": "MXN"},
    "USDMYR": {"name": "USD/MYR", "flag": "🇺🇸🇲🇾", "base": "USD", "quote": "MYR"},
    "USDTHB": {"name": "USD/THB", "flag": "🇺🇸🇹🇭", "base": "USD", "quote": "THB"},
    "USDIDR": {"name": "USD/IDR", "flag": "🇺🇸🇮🇩", "base": "USD", "quote": "IDR"},
    "USDPHP": {"name": "USD/PHP", "flag": "🇺🇸🇵🇭", "base": "USD", "quote": "PHP"},
    "USDEGP": {"name": "USD/EGP", "flag": "🇺🇸🇪🇬", "base": "USD", "quote": "EGP"},
    "USDPKR": {"name": "USD/PKR", "flag": "🇺🇸🇵🇰", "base": "USD", "quote": "PKR"},
    "USDVND": {"name": "USD/VND", "flag": "🇺🇸🇻🇳", "base": "USD", "quote": "VND"},
    "USDARS": {"name": "USD/ARS", "flag": "🇺🇸🇦🇷", "base": "USD", "quote": "ARS"},
    "USDCLP": {"name": "USD/CLP", "flag": "🇺🇸🇨🇱", "base": "USD", "quote": "CLP"},
    "USDCOP": {"name": "USD/COP", "flag": "🇺🇸🇨🇴", "base": "USD", "quote": "COP"},
    "USDBDT": {"name": "USD/BDT", "flag": "🇺🇸🇧🇩", "base": "USD", "quote": "BDT"},
    "USDDZD": {"name": "USD/DZD", "flag": "🇺🇸🇩🇿", "base": "USD", "quote": "DZD"},
}

# ─── INDICES  (Twelve Data) ───────────────────────────────────────────────────
INDICES_PAIRS = {
    "SPX":      {"name": "S&P 500",       "flag": "🇺🇸📈"},
    "NDX":      {"name": "NASDAQ-100",    "flag": "🇺🇸💻"},
    "DJI":      {"name": "Dow Jones 30",  "flag": "🇺🇸🏭"},
    "FTSE":     {"name": "FTSE 100",      "flag": "🇬🇧📊"},
    "DAX":      {"name": "DAX 30",        "flag": "🇩🇪📊"},
    "CAC":      {"name": "CAC 40",        "flag": "🇫🇷📊"},
    "N225":     {"name": "Nikkei 225",    "flag": "🇯🇵📊"},
    "ASX200":   {"name": "ASX 200",       "flag": "🇦🇺📊"},
    "HSI":      {"name": "Hang Seng",     "flag": "🇭🇰📊"},
    "STOXX50E": {"name": "EuroStoxx 50",  "flag": "🇪🇺📊"},
}

# ─── COMMODITIES  (Twelve Data) ──────────────────────────────────────────────
COMMODITIES_PAIRS = {
    "XAU/USD":    {"name": "Gold",         "flag": "🥇"},
    "XAG/USD":    {"name": "Silver",       "flag": "🥈"},
    "WTI/USD":    {"name": "WTI Crude",    "flag": "🛢️"},
    "BRENT/USD":  {"name": "Brent Crude",  "flag": "🛢️"},
    "NATGAS/USD": {"name": "Natural Gas",  "flag": "⛽"},
    "XPT/USD":    {"name": "Platinum",     "flag": "⬜"},
    "XPD/USD":    {"name": "Palladium",    "flag": "🔳"},
}

# ─── STOCKS  (Twelve Data) ───────────────────────────────────────────────────
STOCKS_PAIRS = {
    "AAPL":  {"name": "Apple",           "flag": "🍎"},
    "MSFT":  {"name": "Microsoft",       "flag": "🪟"},
    "GOOGL": {"name": "Alphabet/Google", "flag": "🔍"},
    "AMZN":  {"name": "Amazon",          "flag": "📦"},
    "TSLA":  {"name": "Tesla",           "flag": "⚡"},
    "NVDA":  {"name": "NVIDIA",          "flag": "🟩"},
    "META":  {"name": "Meta",            "flag": "📘"},
    "JPM":   {"name": "JPMorgan",        "flag": "🏛️"},
    "NFLX":  {"name": "Netflix",         "flag": "🎬"},
    "AMD":   {"name": "AMD",             "flag": "🔴"},
    "INTC":  {"name": "Intel",           "flag": "🔲"},
    "BABA":  {"name": "Alibaba",         "flag": "🛍️"},
    "XOM":   {"name": "ExxonMobil",      "flag": "🛢️"},
    "V":     {"name": "VISA",            "flag": "💳"},
    "BA":    {"name": "Boeing",          "flag": "✈️"},
    "CSCO":  {"name": "Cisco",           "flag": "🔌"},
    "JNJ":   {"name": "J&J",             "flag": "💊"},
    "MCD":   {"name": "McDonald's",      "flag": "🍔"},
    "PFE":   {"name": "Pfizer",          "flag": "💉"},
    "C":     {"name": "Citigroup",       "flag": "🏦"},
    "AXP":   {"name": "Amex",            "flag": "💳"},
    "COIN":  {"name": "Coinbase",        "flag": "🪙"},
    "PLTR":  {"name": "Palantir",        "flag": "🔭"},
    "GME":   {"name": "GameStop",        "flag": "🎮"},
    "FDX":   {"name": "FedEx",           "flag": "🚚"},
    "MARA":  {"name": "Marathon Digital","flag": "⛏️"},
}

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_all_pairs() -> dict:
    return {
        "crypto":      CRYPTO_PAIRS,
        "forex":       FOREX_PAIRS,
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
    result = []
    for cat, pairs in get_all_pairs().items():
        for sym in pairs:
            result.append((cat, sym))
    return result

def resolve_fetch_symbol(category: str, symbol: str) -> str:
    """No OTC mapping needed anymore — every symbol IS its fetch symbol."""
    return symbol
