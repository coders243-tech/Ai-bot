# config.py  –  Forex Crypto Signal Bot v3
# Pairs matched exactly to Pocket Option platform (from user screenshots)

# ─── RSI SETTINGS ────────────────────────────────────────────────────────────
RSI_PERIOD        = 14
RSI_OVERSOLD      = 35    # BUY  signal threshold
RSI_OVERBOUGHT    = 65    # SELL signal threshold
MIN_PRICE_HISTORY = 15

# ─── SCAN / SIGNAL SETTINGS ──────────────────────────────────────────────────
SCAN_INTERVAL_MIN      = 10
SCAN_INTERVAL_MAX      = 12
COOLDOWN_SECONDS       = 300    # 5-min cooldown per pair
TRADE_DURATION_DEFAULT = 5
CONFIDENCE_DEFAULT     = 50
MARTINGALE_LEVELS      = 3
MARTINGALE_GAP_MIN     = 3
TP_SL_PCT              = 0.005  # 0.5%

# ─── TIMEZONE ────────────────────────────────────────────────────────────────
TIMEZONE_NAME   = "WAT"
TIMEZONE_OFFSET = 1  # UTC+1

# ─── CRYPTO PAIRS  (CoinGecko batch fetch) ───────────────────────────────────
# Matched to Pocket Option Cryptocurrencies tab
CRYPTO_PAIRS = {
    "BTCUSDT":   {"name": "Bitcoin",        "flag": "🟡",  "cg_id": "bitcoin"},
    "ETHUSDT":   {"name": "Ethereum",       "flag": "🔷",  "cg_id": "ethereum"},
    "LTCUSDT":   {"name": "Litecoin",       "flag": "⚪",  "cg_id": "litecoin"},
    "DOGEUSDT":  {"name": "Dogecoin",       "flag": "🐶",  "cg_id": "dogecoin"},
    "DOTUSDT":   {"name": "Polkadot",       "flag": "⚫",  "cg_id": "polkadot"},
    "SOLUSDT":   {"name": "Solana",         "flag": "🟣",  "cg_id": "solana"},
    "ADAUSDT":   {"name": "Cardano",        "flag": "💙",  "cg_id": "cardano"},
    "MATICUSDT": {"name": "Polygon",        "flag": "🟪",  "cg_id": "matic-network"},
    "AVAXUSDT":  {"name": "Avalanche",      "flag": "🔺",  "cg_id": "avalanche-2"},
    "XRPUSDT":   {"name": "Ripple/XRP",     "flag": "🔵",  "cg_id": "ripple"},
    "BNBUSDT":   {"name": "BNB",            "flag": "🟨",  "cg_id": "binancecoin"},
    "TRXUSDT":   {"name": "TRON",           "flag": "🔴",  "cg_id": "tron"},
    "TONUSDT":   {"name": "Toncoin",        "flag": "💎",  "cg_id": "the-open-network"},
}

# ─── FOREX PAIRS  (Alpha Vantage CURRENCY_EXCHANGE_RATE) ─────────────────────
# All pairs visible in your Pocket Option Currencies screenshots
FOREX_PAIRS = {
    # ── Majors ───────────────────────────────────────────────────────────────
    "EURUSD": {"name": "EUR/USD", "flag": "🇪🇺🇺🇸", "from": "EUR", "to": "USD"},
    "GBPUSD": {"name": "GBP/USD", "flag": "🇬🇧🇺🇸", "from": "GBP", "to": "USD"},
    "USDJPY": {"name": "USD/JPY", "flag": "🇺🇸🇯🇵", "from": "USD", "to": "JPY"},
    "USDCHF": {"name": "USD/CHF", "flag": "🇺🇸🇨🇭", "from": "USD", "to": "CHF"},
    "AUDUSD": {"name": "AUD/USD", "flag": "🇦🇺🇺🇸", "from": "AUD", "to": "USD"},
    "USDCAD": {"name": "USD/CAD", "flag": "🇺🇸🇨🇦", "from": "USD", "to": "CAD"},
    "NZDUSD": {"name": "NZD/USD", "flag": "🇳🇿🇺🇸", "from": "NZD", "to": "USD"},
    # ── EUR crosses ──────────────────────────────────────────────────────────
    "EURGBP": {"name": "EUR/GBP", "flag": "🇪🇺🇬🇧", "from": "EUR", "to": "GBP"},
    "EURJPY": {"name": "EUR/JPY", "flag": "🇪🇺🇯🇵", "from": "EUR", "to": "JPY"},
    "EURCHF": {"name": "EUR/CHF", "flag": "🇪🇺🇨🇭", "from": "EUR", "to": "CHF"},
    "EURCAD": {"name": "EUR/CAD", "flag": "🇪🇺🇨🇦", "from": "EUR", "to": "CAD"},
    "EURAUD": {"name": "EUR/AUD", "flag": "🇪🇺🇦🇺", "from": "EUR", "to": "AUD"},
    "EURNZD": {"name": "EUR/NZD", "flag": "🇪🇺🇳🇿", "from": "EUR", "to": "NZD"},
    "EURTRY": {"name": "EUR/TRY", "flag": "🇪🇺🇹🇷", "from": "EUR", "to": "TRY"},
    "EURHUF": {"name": "EUR/HUF", "flag": "🇪🇺🇭🇺", "from": "EUR", "to": "HUF"},
    "EURRUB": {"name": "EUR/RUB", "flag": "🇪🇺🇷🇺", "from": "EUR", "to": "RUB"},
    # ── GBP crosses ──────────────────────────────────────────────────────────
    "GBPJPY": {"name": "GBP/JPY", "flag": "🇬🇧🇯🇵", "from": "GBP", "to": "JPY"},
    "GBPAUD": {"name": "GBP/AUD", "flag": "🇬🇧🇦🇺", "from": "GBP", "to": "AUD"},
    "GBPCAD": {"name": "GBP/CAD", "flag": "🇬🇧🇨🇦", "from": "GBP", "to": "CAD"},
    "GBPCHF": {"name": "GBP/CHF", "flag": "🇬🇧🇨🇭", "from": "GBP", "to": "CHF"},
    "GBPNZD": {"name": "GBP/NZD", "flag": "🇬🇧🇳🇿", "from": "GBP", "to": "NZD"},
    # ── AUD crosses ──────────────────────────────────────────────────────────
    "AUDJPY": {"name": "AUD/JPY", "flag": "🇦🇺🇯🇵", "from": "AUD", "to": "JPY"},
    "AUDCAD": {"name": "AUD/CAD", "flag": "🇦🇺🇨🇦", "from": "AUD", "to": "CAD"},
    "AUDNZD": {"name": "AUD/NZD", "flag": "🇦🇺🇳🇿", "from": "AUD", "to": "NZD"},
    "AUDCHF": {"name": "AUD/CHF", "flag": "🇦🇺🇨🇭", "from": "AUD", "to": "CHF"},
    # ── CAD / CHF / NZD crosses ──────────────────────────────────────────────
    "CADJPY": {"name": "CAD/JPY", "flag": "🇨🇦🇯🇵", "from": "CAD", "to": "JPY"},
    "CADCHF": {"name": "CAD/CHF", "flag": "🇨🇦🇨🇭", "from": "CAD", "to": "CHF"},
    "CHFJPY": {"name": "CHF/JPY", "flag": "🇨🇭🇯🇵", "from": "CHF", "to": "JPY"},
    "CHFNOK": {"name": "CHF/NOK", "flag": "🇨🇭🇳🇴", "from": "CHF", "to": "NOK"},
    "NZDJPY": {"name": "NZD/JPY", "flag": "🇳🇿🇯🇵", "from": "NZD", "to": "JPY"},
    # ── African & emerging market pairs ──────────────────────────────────────
    "USDNGN": {"name": "USD/NGN", "flag": "🇺🇸🇳🇬", "from": "USD", "to": "NGN"},
    "USDKES": {"name": "USD/KES", "flag": "🇺🇸🇰🇪", "from": "USD", "to": "KES"},
    "USDZAR": {"name": "USD/ZAR", "flag": "🇺🇸🇿🇦", "from": "USD", "to": "ZAR"},
    "USDINR": {"name": "USD/INR", "flag": "🇺🇸🇮🇳", "from": "USD", "to": "INR"},
    "USDRUB": {"name": "USD/RUB", "flag": "🇺🇸🇷🇺", "from": "USD", "to": "RUB"},
    "USDSGD": {"name": "USD/SGD", "flag": "🇺🇸🇸🇬", "from": "USD", "to": "SGD"},
    "USDPHP": {"name": "USD/PHP", "flag": "🇺🇸🇵🇭", "from": "USD", "to": "PHP"},
    "USDMXN": {"name": "USD/MXN", "flag": "🇺🇸🇲🇽", "from": "USD", "to": "MXN"},
    "USDARS": {"name": "USD/ARS", "flag": "🇺🇸🇦🇷", "from": "USD", "to": "ARS"},
    "USDVND": {"name": "USD/VND", "flag": "🇺🇸🇻🇳", "from": "USD", "to": "VND"},
    "USDMYR": {"name": "USD/MYR", "flag": "🇺🇸🇲🇾", "from": "USD", "to": "MYR"},
    "USDTHB": {"name": "USD/THB", "flag": "🇺🇸🇹🇭", "from": "USD", "to": "THB"},
    "USDBDT": {"name": "USD/BDT", "flag": "🇺🇸🇧🇩", "from": "USD", "to": "BDT"},
    "USDDZD": {"name": "USD/DZD", "flag": "🇺🇸🇩🇿", "from": "USD", "to": "DZD"},
    "USDEGP": {"name": "USD/EGP", "flag": "🇺🇸🇪🇬", "from": "USD", "to": "EGP"},
    "USDIDR": {"name": "USD/IDR", "flag": "🇺🇸🇮🇩", "from": "USD", "to": "IDR"},
    "USDCOP": {"name": "USD/COP", "flag": "🇺🇸🇨🇴", "from": "USD", "to": "COP"},
    "USDCLP": {"name": "USD/CLP", "flag": "🇺🇸🇨🇱", "from": "USD", "to": "CLP"},
    "USDPKR": {"name": "USD/PKR", "flag": "🇺🇸🇵🇰", "from": "USD", "to": "PKR"},
    "USDCNH": {"name": "USD/CNH", "flag": "🇺🇸🇨🇳", "from": "USD", "to": "CNH"},
    # ── Middle East / exotic ─────────────────────────────────────────────────
    "AEDCNY": {"name": "AED/CNY", "flag": "🇦🇪🇨🇳", "from": "AED", "to": "CNY"},
    "OMRCNY": {"name": "OMR/CNY", "flag": "🇴🇲🇨🇳", "from": "OMR", "to": "CNY"},
    "SARCNY": {"name": "SAR/CNY", "flag": "🇸🇦🇨🇳", "from": "SAR", "to": "CNY"},
    "QARCNY": {"name": "QAR/CNY", "flag": "🇶🇦🇨🇳", "from": "QAR", "to": "CNY"},
    "JODCNY": {"name": "JOD/CNY", "flag": "🇯🇴🇨🇳", "from": "JOD", "to": "CNY"},
    "MADUSD": {"name": "MAD/USD", "flag": "🇲🇦🇺🇸", "from": "MAD", "to": "USD"},
    "TNDUSD": {"name": "TND/USD", "flag": "🇹🇳🇺🇸", "from": "TND", "to": "USD"},
    "YERUSD": {"name": "YER/USD", "flag": "🇾🇪🇺🇸", "from": "YER", "to": "USD"},
    "LBPUSD": {"name": "LBP/USD", "flag": "🇱🇧🇺🇸", "from": "LBP", "to": "USD"},
    "UAHUSD": {"name": "UAH/USD", "flag": "🇺🇦🇺🇸", "from": "UAH", "to": "USD"},
    "ZARUSD": {"name": "ZAR/USD", "flag": "🇿🇦🇺🇸", "from": "ZAR", "to": "USD"},
    "NGНUSD": {"name": "NGN/USD", "flag": "🇳🇬🇺🇸", "from": "NGN", "to": "USD"},
    "KESUSD": {"name": "KES/USD", "flag": "🇰🇪🇺🇸", "from": "KES", "to": "USD"},
}

# ─── INDICES  (Alpha Vantage GLOBAL_QUOTE via ETF proxies) ───────────────────
# Matched to Pocket Option Indices tab
INDICES_PAIRS = {
    "SPY":  {"name": "SP500 (S&P 500)",        "flag": "🇺🇸📈"},
    "QQQ":  {"name": "US100 (NASDAQ-100)",     "flag": "🇺🇸💻"},
    "DIA":  {"name": "DJI30 (Dow Jones 30)",   "flag": "🇺🇸🏭"},
    "EWU":  {"name": "100GBP (FTSE 100)",      "flag": "🇬🇧📊"},
    "EWG":  {"name": "D30EUR (DAX 30)",        "flag": "🇩🇪📊"},
    "EWQ":  {"name": "F40EUR (CAC 40)",        "flag": "🇫🇷📊"},
    "EWI":  {"name": "E35EUR (IBEX 35)",       "flag": "🇪🇸📊"},
    "EZU":  {"name": "E50EUR (EuroStoxx 50)",  "flag": "🇪🇺📊"},
    "EWJ":  {"name": "JPN225 (Nikkei 225)",    "flag": "🇯🇵📊"},
    "EWZ":  {"name": "AUS200 (ASX 200)",       "flag": "🇦🇺📊"},
    "FXI":  {"name": "HK33 (Hang Seng 33)",    "flag": "🇭🇰📊"},
    "EWP":  {"name": "AEX 25 (Netherlands)",   "flag": "🇳🇱📊"},
}

# ─── COMMODITIES  (Alpha Vantage GLOBAL_QUOTE via ETF proxies) ───────────────
# Matched to Pocket Option Commodities tab
COMMODITIES_PAIRS = {
    "GLD":  {"name": "Gold (XAU)",          "flag": "🥇"},
    "SLV":  {"name": "Silver (XAG)",        "flag": "🥈"},
    "USO":  {"name": "WTI Crude Oil",       "flag": "🛢️"},
    "BNO":  {"name": "Brent Crude Oil",     "flag": "🛢️"},
    "UNG":  {"name": "Natural Gas",         "flag": "⛽"},
    "PPLT": {"name": "Platinum spot",       "flag": "⬜"},
    "PALL": {"name": "Palladium spot",      "flag": "🔳"},
}

# ─── STOCKS  (Alpha Vantage GLOBAL_QUOTE) ────────────────────────────────────
# All stocks visible in your Pocket Option Stocks screenshots
STOCKS_PAIRS = {
    # 92% payout OTC stocks (highest priority)
    "AAPL":  {"name": "Apple OTC",                 "flag": "🍎"},
    "AXP":   {"name": "American Express OTC",      "flag": "💳"},
    "INTC":  {"name": "Intel OTC",                 "flag": "🔲"},
    "MCD":   {"name": "McDonald's OTC",            "flag": "🍔"},
    "XOM":   {"name": "ExxonMobil OTC",            "flag": "🛢️"},
    "NFLX":  {"name": "Netflix OTC",               "flag": "🎬"},
    "PLTR":  {"name": "Palantir Technologies OTC", "flag": "🔭"},
    "TSLA":  {"name": "Tesla OTC",                 "flag": "⚡"},
    "MSFT":  {"name": "Microsoft OTC",             "flag": "🪟"},
    "META":  {"name": "Meta / Facebook OTC",       "flag": "📘"},
    "AMD":   {"name": "Advanced Micro Devices OTC","flag": "🔴"},
    "BABA":  {"name": "Alibaba OTC",               "flag": "🛍️"},
    "JPM":   {"name": "JPMorgan Chase OTC",        "flag": "🏛️"},
    "NVDA":  {"name": "NVIDIA OTC",                "flag": "🟩"},
    "GOOGL": {"name": "Alphabet / Google OTC",     "flag": "🔍"},
    "AMZN":  {"name": "Amazon OTC",                "flag": "📦"},
    "COIN":  {"name": "Coinbase Global OTC",       "flag": "🪙"},
    "GME":   {"name": "GameStop Corp OTC",         "flag": "🎮"},
    "PFE":   {"name": "Pfizer Inc OTC",            "flag": "💉"},
    "C":     {"name": "Citigroup Inc OTC",         "flag": "🏦"},
    "V":     {"name": "VISA OTC",                  "flag": "💳"},
    "BA":    {"name": "Boeing Company OTC",        "flag": "✈️"},
    "CSCO":  {"name": "Cisco OTC",                 "flag": "🔌"},
    "JNJ":   {"name": "Johnson & Johnson OTC",     "flag": "💊"},
    "FDX":   {"name": "FedEx OTC",                 "flag": "🚚"},
    "MARA":  {"name": "Marathon Digital Holdings", "flag": "⛏️"},
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
    """Return (category, symbol_key, pair_info) or (None, None, None)."""
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
