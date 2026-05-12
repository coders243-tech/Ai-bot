# config.py  –  Forex Crypto Signal Bot v4
# Data sources:
#   Crypto        → CoinGecko (free, no key, Railway-friendly)
#   Forex         → ExchangeRate-API (free, no key, Railway-friendly)
#   Stocks        → Twelve Data (free tier, API key, Railway-friendly)
#   Indices       → Twelve Data (free tier, API key, Railway-friendly)
#   Commodities   → Metals-API for gold/silver + Twelve Data for others

# ─── RSI SETTINGS ────────────────────────────────────────────────────────────
RSI_PERIOD        = 14
RSI_OVERSOLD      = 35
RSI_OVERBOUGHT    = 65
MIN_PRICE_HISTORY = 15

# ─── SCAN / SIGNAL SETTINGS ──────────────────────────────────────────────────
SCAN_INTERVAL_MIN      = 10
SCAN_INTERVAL_MAX      = 12
COOLDOWN_SECONDS       = 300
TRADE_DURATION_DEFAULT = 5
CONFIDENCE_DEFAULT     = 50
MARTINGALE_LEVELS      = 3
MARTINGALE_GAP_MIN     = 3
TP_SL_PCT              = 0.005

# ─── TIMEZONE ────────────────────────────────────────────────────────────────
TIMEZONE_NAME   = "WAT"
TIMEZONE_OFFSET = 1  # UTC+1

# ─── CRYPTO PAIRS  (CoinGecko — free, no key) ────────────────────────────────
CRYPTO_PAIRS = {
    "BTCUSDT":   {"name": "Bitcoin",        "flag": "🟡", "cg_id": "bitcoin"},
    "ETHUSDT":   {"name": "Ethereum",       "flag": "🔷", "cg_id": "ethereum"},
    "LTCUSDT":   {"name": "Litecoin",       "flag": "⚪", "cg_id": "litecoin"},
    "DOGEUSDT":  {"name": "Dogecoin",       "flag": "🐶", "cg_id": "dogecoin"},
    "DOTUSDT":   {"name": "Polkadot",       "flag": "⚫", "cg_id": "polkadot"},
    "SOLUSDT":   {"name": "Solana",         "flag": "🟣", "cg_id": "solana"},
    "ADAUSDT":   {"name": "Cardano",        "flag": "💙", "cg_id": "cardano"},
    "MATICUSDT": {"name": "Polygon",        "flag": "🟪", "cg_id": "matic-network"},
    "AVAXUSDT":  {"name": "Avalanche",      "flag": "🔺", "cg_id": "avalanche-2"},
    "XRPUSDT":   {"name": "Ripple/XRP",     "flag": "🔵", "cg_id": "ripple"},
    "BNBUSDT":   {"name": "BNB",            "flag": "🟨", "cg_id": "binancecoin"},
    "TRXUSDT":   {"name": "TRON",           "flag": "🔴", "cg_id": "tron"},
    "TONUSDT":   {"name": "Toncoin",        "flag": "💎", "cg_id": "the-open-network"},
}

# ─── FOREX PAIRS  (ExchangeRate-API — free, no key needed) ───────────────────
# Uses open.er-api.com which is completely free and Railway-friendly
# Format: base currency — we always fetch against USD base
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
    "EURHUF": {"name": "EUR/HUF", "flag": "🇪🇺🇭🇺", "base": "EUR", "quote": "HUF"},
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
    "USDPHP": {"name": "USD/PHP", "flag": "🇺🇸🇵🇭", "base": "USD", "quote": "PHP"},
    "USDMXN": {"name": "USD/MXN", "flag": "🇺🇸🇲🇽", "base": "USD", "quote": "MXN"},
    "USDMYR": {"name": "USD/MYR", "flag": "🇺🇸🇲🇾", "base": "USD", "quote": "MYR"},
    "USDTHB": {"name": "USD/THB", "flag": "🇺🇸🇹🇭", "base": "USD", "quote": "THB"},
    "USDIDR": {"name": "USD/IDR", "flag": "🇺🇸🇮🇩", "base": "USD", "quote": "IDR"},
    "USDEGP": {"name": "USD/EGP", "flag": "🇺🇸🇪🇬", "base": "USD", "quote": "EGP"},
    "USDPKR": {"name": "USD/PKR", "flag": "🇺🇸🇵🇰", "base": "USD", "quote": "PKR"},
    "USDVND": {"name": "USD/VND", "flag": "🇺🇸🇻🇳", "base": "USD", "quote": "VND"},
    "USDARS": {"name": "USD/ARS", "flag": "🇺🇸🇦🇷", "base": "USD", "quote": "ARS"},
    "USDCLP": {"name": "USD/CLP", "flag": "🇺🇸🇨🇱", "base": "USD", "quote": "CLP"},
    "USDCOP": {"name": "USD/COP", "flag": "🇺🇸🇨🇴", "base": "USD", "quote": "COP"},
    "USDBDT": {"name": "USD/BDT", "flag": "🇺🇸🇧🇩", "base": "USD", "quote": "BDT"},
    "USDDZD": {"name": "USD/DZD", "flag": "🇺🇸🇩🇿", "base": "USD", "quote": "DZD"},
}

# ─── INDICES  (Twelve Data — free tier, needs TWELVE_DATA_KEY) ───────────────
# Using real index symbols supported by Twelve Data free tier
INDICES_PAIRS = {
    "SPX":    {"name": "SP500  (S&P 500)",       "flag": "🇺🇸📈"},
    "NDX":    {"name": "US100  (NASDAQ-100)",     "flag": "🇺🇸💻"},
    "DJI":    {"name": "DJI30  (Dow Jones)",      "flag": "🇺🇸🏭"},
    "FTSE":   {"name": "100GBP (FTSE 100)",       "flag": "🇬🇧📊"},
    "DAX":    {"name": "D30EUR (DAX 30)",         "flag": "🇩🇪📊"},
    "CAC":    {"name": "F40EUR (CAC 40)",         "flag": "🇫🇷📊"},
    "N225":   {"name": "JPN225 (Nikkei 225)",     "flag": "🇯🇵📊"},
    "ASX200": {"name": "AUS200 (ASX 200)",        "flag": "🇦🇺📊"},
    "HSI":    {"name": "HK33   (Hang Seng)",      "flag": "🇭🇰📊"},
    "STOXX50":{"name": "E50EUR (EuroStoxx 50)",   "flag": "🇪🇺📊"},
}

# ─── COMMODITIES  (Twelve Data) ──────────────────────────────────────────────
COMMODITIES_PAIRS = {
    "XAU/USD": {"name": "Gold  (XAU/USD)",      "flag": "🥇"},
    "XAG/USD": {"name": "Silver (XAG/USD)",     "flag": "🥈"},
    "WTI/USD": {"name": "WTI Crude Oil",        "flag": "🛢️"},
    "BRENT/USD":{"name": "Brent Crude Oil",     "flag": "🛢️"},
    "NATGAS/USD":{"name": "Natural Gas",        "flag": "⛽"},
    "XPT/USD": {"name": "Platinum spot",        "flag": "⬜"},
    "XPD/USD": {"name": "Palladium spot",       "flag": "🔳"},
}

# ─── STOCKS  (Twelve Data — free tier) ───────────────────────────────────────
STOCKS_PAIRS = {
    "AAPL":  {"name": "Apple OTC",                  "flag": "🍎"},
    "AXP":   {"name": "American Express OTC",       "flag": "💳"},
    "INTC":  {"name": "Intel OTC",                  "flag": "🔲"},
    "MCD":   {"name": "McDonald's OTC",             "flag": "🍔"},
    "XOM":   {"name": "ExxonMobil OTC",             "flag": "🛢️"},
    "NFLX":  {"name": "Netflix OTC",                "flag": "🎬"},
    "PLTR":  {"name": "Palantir Technologies OTC",  "flag": "🔭"},
    "TSLA":  {"name": "Tesla OTC",                  "flag": "⚡"},
    "MSFT":  {"name": "Microsoft OTC",              "flag": "🪟"},
    "META":  {"name": "Meta / Facebook OTC",        "flag": "📘"},
    "AMD":   {"name": "Advanced Micro Devices OTC", "flag": "🔴"},
    "BABA":  {"name": "Alibaba OTC",                "flag": "🛍️"},
    "JPM":   {"name": "JPMorgan Chase OTC",         "flag": "🏛️"},
    "NVDA":  {"name": "NVIDIA OTC",                 "flag": "🟩"},
    "GOOGL": {"name": "Alphabet / Google OTC",      "flag": "🔍"},
    "AMZN":  {"name": "Amazon OTC",                 "flag": "📦"},
    "COIN":  {"name": "Coinbase Global OTC",        "flag": "🪙"},
    "GME":   {"name": "GameStop Corp OTC",          "flag": "🎮"},
    "PFE":   {"name": "Pfizer Inc OTC",             "flag": "💉"},
    "C":     {"name": "Citigroup Inc OTC",          "flag": "🏦"},
    "V":     {"name": "VISA OTC",                   "flag": "💳"},
    "BA":    {"name": "Boeing Company OTC",         "flag": "✈️"},
    "CSCO":  {"name": "Cisco OTC",                  "flag": "🔌"},
    "JNJ":   {"name": "Johnson & Johnson OTC",      "flag": "💊"},
    "FDX":   {"name": "FedEx OTC",                  "flag": "🚚"},
    "MARA":  {"name": "Marathon Digital Holdings",  "flag": "⛏️"},
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