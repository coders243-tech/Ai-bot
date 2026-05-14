# config.py  –  Forex Crypto Signal Bot v6
#
# OTC PAIRS NOTE:
#   Pocket Option OTC instruments are broker-synthetic — no external API
#   carries their exact prices. This bot uses the underlying real pair
#   price feed and clearly labels signals as OTC. Price behaviour is
#   closely correlated. A disclaimer is shown on every OTC signal.

# ─── RSI SETTINGS ────────────────────────────────────────────────────────────
RSI_PERIOD        = 14
RSI_OVERSOLD      = 35
RSI_OVERBOUGHT    = 65
MIN_PRICE_HISTORY = 15

# ─── SCAN SETTINGS ───────────────────────────────────────────────────────────
SCAN_INTERVAL_MIN    = 10
SCAN_INTERVAL_MAX    = 12
COOLDOWN_SECONDS     = 300
CONFIDENCE_DEFAULT   = 50
MARTINGALE_LEVELS    = 3
MARTINGALE_GAP_MIN   = 3
TP_SL_PCT            = 0.005
MAX_SIGNALS_PER_SCAN = 3

# ─── DYNAMIC DURATION ────────────────────────────────────────────────────────
# Duration is chosen per signal based on how extreme the RSI is.
# The further RSI is from neutral, the faster the expected reversal,
# so we use a shorter duration. Mild crossings get more time to play out.
#
#  RSI distance from threshold:
#    > 15 points  →  EXTREME  → 1–2 min  (very fast reversal expected)
#    8–15 points  →  STRONG   → 3–5 min
#    0–8  points  →  MILD     → 5–10 min (slower, needs more time)
DURATION_EXTREME_MAX = 2    # minutes
DURATION_STRONG_MAX  = 5    # minutes
DURATION_MILD_MAX    = 10   # minutes
DURATION_EXTREME_MIN = 1
DURATION_STRONG_MIN  = 3
DURATION_MILD_MIN    = 5

# ─── TIMEZONE ────────────────────────────────────────────────────────────────
TIMEZONE_NAME   = "WAT"
TIMEZONE_OFFSET = 1  # UTC+1

# ─── CRYPTO PAIRS  (CoinGecko) ───────────────────────────────────────────────
# otc=True  → signal labelled as OTC, price from same CoinGecko feed
CRYPTO_PAIRS = {
    # Regular
    "BTCUSDT":   {"name": "Bitcoin",      "flag": "🟡", "cg_id": "bitcoin",        "otc": False},
    "ETHUSDT":   {"name": "Ethereum",     "flag": "🔷", "cg_id": "ethereum",       "otc": False},
    "LTCUSDT":   {"name": "Litecoin",     "flag": "⚪", "cg_id": "litecoin",       "otc": False},
    "DOGEUSDT":  {"name": "Dogecoin",     "flag": "🐶", "cg_id": "dogecoin",       "otc": False},
    "DOTUSDT":   {"name": "Polkadot",     "flag": "⚫", "cg_id": "polkadot",       "otc": False},
    "SOLUSDT":   {"name": "Solana",       "flag": "🟣", "cg_id": "solana",         "otc": False},
    "ADAUSDT":   {"name": "Cardano",      "flag": "💙", "cg_id": "cardano",        "otc": False},
    "MATICUSDT": {"name": "Polygon",      "flag": "🟪", "cg_id": "matic-network",  "otc": False},
    "AVAXUSDT":  {"name": "Avalanche",    "flag": "🔺", "cg_id": "avalanche-2",    "otc": False},
    "XRPUSDT":   {"name": "Ripple/XRP",   "flag": "🔵", "cg_id": "ripple",         "otc": False},
    "BNBUSDT":   {"name": "BNB",          "flag": "🟨", "cg_id": "binancecoin",    "otc": False},
    "TRXUSDT":   {"name": "TRON",         "flag": "🔴", "cg_id": "tron",           "otc": False},
    "TONUSDT":   {"name": "Toncoin",      "flag": "💎", "cg_id": "the-open-network","otc": False},
    # OTC  (same CoinGecko feed, labelled OTC)
    "BTCOTC":    {"name": "Bitcoin OTC",  "flag": "🟡", "cg_id": "bitcoin",        "otc": True},
    "ETHOTC":    {"name": "Ethereum OTC", "flag": "🔷", "cg_id": "ethereum",       "otc": True},
    "LTCOTC":    {"name": "Litecoin OTC", "flag": "⚪", "cg_id": "litecoin",       "otc": True},
    "DOGEOTC":   {"name": "Dogecoin OTC", "flag": "🐶", "cg_id": "dogecoin",       "otc": True},
    "DOTOTC":    {"name": "Polkadot OTC", "flag": "⚫", "cg_id": "polkadot",       "otc": True},
    "SOLOТC":    {"name": "Solana OTC",   "flag": "🟣", "cg_id": "solana",         "otc": True},
    "ADAOTC":    {"name": "Cardano OTC",  "flag": "💙", "cg_id": "cardano",        "otc": True},
    "AVAXOTC":   {"name": "Avalanche OTC","flag": "🔺", "cg_id": "avalanche-2",    "otc": True},
    "TRXOTC":    {"name": "TRON OTC",     "flag": "🔴", "cg_id": "tron",           "otc": True},
    "TONOTC":    {"name": "Toncoin OTC",  "flag": "💎", "cg_id": "the-open-network","otc": True},
}

# ─── FOREX PAIRS  (open.er-api.com) ──────────────────────────────────────────
FOREX_PAIRS = {
    # ── Majors ───────────────────────────────────────────────────────────────
    "EURUSD":    {"name": "EUR/USD",     "flag": "🇪🇺🇺🇸", "base": "EUR", "quote": "USD", "otc": False},
    "GBPUSD":    {"name": "GBP/USD",     "flag": "🇬🇧🇺🇸", "base": "GBP", "quote": "USD", "otc": False},
    "USDJPY":    {"name": "USD/JPY",     "flag": "🇺🇸🇯🇵", "base": "USD", "quote": "JPY", "otc": False},
    "USDCHF":    {"name": "USD/CHF",     "flag": "🇺🇸🇨🇭", "base": "USD", "quote": "CHF", "otc": False},
    "AUDUSD":    {"name": "AUD/USD",     "flag": "🇦🇺🇺🇸", "base": "AUD", "quote": "USD", "otc": False},
    "USDCAD":    {"name": "USD/CAD",     "flag": "🇺🇸🇨🇦", "base": "USD", "quote": "CAD", "otc": False},
    "NZDUSD":    {"name": "NZD/USD",     "flag": "🇳🇿🇺🇸", "base": "NZD", "quote": "USD", "otc": False},
    # ── Majors OTC ───────────────────────────────────────────────────────────
    "EURUSDOTC": {"name": "EUR/USD OTC", "flag": "🇪🇺🇺🇸", "base": "EUR", "quote": "USD", "otc": True},
    "GBPUSDOTC": {"name": "GBP/USD OTC", "flag": "🇬🇧🇺🇸", "base": "GBP", "quote": "USD", "otc": True},
    "USDJPYOTC": {"name": "USD/JPY OTC", "flag": "🇺🇸🇯🇵", "base": "USD", "quote": "JPY", "otc": True},
    "USDCHFOTC": {"name": "USD/CHF OTC", "flag": "🇺🇸🇨🇭", "base": "USD", "quote": "CHF", "otc": True},
    "AUDUSDOTC": {"name": "AUD/USD OTC", "flag": "🇦🇺🇺🇸", "base": "AUD", "quote": "USD", "otc": True},
    "USDCADOTC": {"name": "USD/CAD OTC", "flag": "🇺🇸🇨🇦", "base": "USD", "quote": "CAD", "otc": True},
    "NZDUSDOTC": {"name": "NZD/USD OTC", "flag": "🇳🇿🇺🇸", "base": "NZD", "quote": "USD", "otc": True},
    # ── EUR crosses ──────────────────────────────────────────────────────────
    "EURGBP":    {"name": "EUR/GBP",     "flag": "🇪🇺🇬🇧", "base": "EUR", "quote": "GBP", "otc": False},
    "EURJPY":    {"name": "EUR/JPY",     "flag": "🇪🇺🇯🇵", "base": "EUR", "quote": "JPY", "otc": False},
    "EURCHF":    {"name": "EUR/CHF",     "flag": "🇪🇺🇨🇭", "base": "EUR", "quote": "CHF", "otc": False},
    "EURCAD":    {"name": "EUR/CAD",     "flag": "🇪🇺🇨🇦", "base": "EUR", "quote": "CAD", "otc": False},
    "EURAUD":    {"name": "EUR/AUD",     "flag": "🇪🇺🇦🇺", "base": "EUR", "quote": "AUD", "otc": False},
    "EURNZD":    {"name": "EUR/NZD",     "flag": "🇪🇺🇳🇿", "base": "EUR", "quote": "NZD", "otc": False},
    # ── EUR crosses OTC ──────────────────────────────────────────────────────
    "EURGBPOTC": {"name": "EUR/GBP OTC", "flag": "🇪🇺🇬🇧", "base": "EUR", "quote": "GBP", "otc": True},
    "EURJPYOTC": {"name": "EUR/JPY OTC", "flag": "🇪🇺🇯🇵", "base": "EUR", "quote": "JPY", "otc": True},
    "EURNZDOTC": {"name": "EUR/NZD OTC", "flag": "🇪🇺🇳🇿", "base": "EUR", "quote": "NZD", "otc": True},
    # ── GBP crosses ──────────────────────────────────────────────────────────
    "GBPJPY":    {"name": "GBP/JPY",     "flag": "🇬🇧🇯🇵", "base": "GBP", "quote": "JPY", "otc": False},
    "GBPAUD":    {"name": "GBP/AUD",     "flag": "🇬🇧🇦🇺", "base": "GBP", "quote": "AUD", "otc": False},
    "GBPCAD":    {"name": "GBP/CAD",     "flag": "🇬🇧🇨🇦", "base": "GBP", "quote": "CAD", "otc": False},
    "GBPCHF":    {"name": "GBP/CHF",     "flag": "🇬🇧🇨🇭", "base": "GBP", "quote": "CHF", "otc": False},
    "GBPNZD":    {"name": "GBP/NZD",     "flag": "🇬🇧🇳🇿", "base": "GBP", "quote": "NZD", "otc": False},
    # ── GBP crosses OTC ──────────────────────────────────────────────────────
    "GBPJPYOTC": {"name": "GBP/JPY OTC", "flag": "🇬🇧🇯🇵", "base": "GBP", "quote": "JPY", "otc": True},
    "GBPAUDOTC": {"name": "GBP/AUD OTC", "flag": "🇬🇧🇦🇺", "base": "GBP", "quote": "AUD", "otc": True},
    "GBPCADOTC": {"name": "GBP/CAD OTC", "flag": "🇬🇧🇨🇦", "base": "GBP", "quote": "CAD", "otc": True},
    # ── AUD crosses ──────────────────────────────────────────────────────────
    "AUDJPY":    {"name": "AUD/JPY",     "flag": "🇦🇺🇯🇵", "base": "AUD", "quote": "JPY", "otc": False},
    "AUDCAD":    {"name": "AUD/CAD",     "flag": "🇦🇺🇨🇦", "base": "AUD", "quote": "CAD", "otc": False},
    "AUDNZD":    {"name": "AUD/NZD",     "flag": "🇦🇺🇳🇿", "base": "AUD", "quote": "NZD", "otc": False},
    "AUDCHF":    {"name": "AUD/CHF",     "flag": "🇦🇺🇨🇭", "base": "AUD", "quote": "CHF", "otc": False},
    # ── AUD crosses OTC ──────────────────────────────────────────────────────
    "AUDJPYOTC": {"name": "AUD/JPY OTC", "flag": "🇦🇺🇯🇵", "base": "AUD", "quote": "JPY", "otc": True},
    "AUDNZDOTC": {"name": "AUD/NZD OTC", "flag": "🇦🇺🇳🇿", "base": "AUD", "quote": "NZD", "otc": True},
    # ── Other crosses ─────────────────────────────────────────────────────────
    "CADJPY":    {"name": "CAD/JPY",     "flag": "🇨🇦🇯🇵", "base": "CAD", "quote": "JPY", "otc": False},
    "CADCHF":    {"name": "CAD/CHF",     "flag": "🇨🇦🇨🇭", "base": "CAD", "quote": "CHF", "otc": False},
    "CHFJPY":    {"name": "CHF/JPY",     "flag": "🇨🇭🇯🇵", "base": "CHF", "quote": "JPY", "otc": False},
    "NZDJPY":    {"name": "NZD/JPY",     "flag": "🇳🇿🇯🇵", "base": "NZD", "quote": "JPY", "otc": False},
    # ── Other crosses OTC ────────────────────────────────────────────────────
    "CADJPYOTC": {"name": "CAD/JPY OTC", "flag": "🇨🇦🇯🇵", "base": "CAD", "quote": "JPY", "otc": True},
    "CHFJPYOTC": {"name": "CHF/JPY OTC", "flag": "🇨🇭🇯🇵", "base": "CHF", "quote": "JPY", "otc": True},
    "NZDJPYOTC": {"name": "NZD/JPY OTC", "flag": "🇳🇿🇯🇵", "base": "NZD", "quote": "JPY", "otc": True},
    # ── African & emerging ────────────────────────────────────────────────────
    "USDNGN":    {"name": "USD/NGN",     "flag": "🇺🇸🇳🇬", "base": "USD", "quote": "NGN", "otc": False},
    "USDKES":    {"name": "USD/KES",     "flag": "🇺🇸🇰🇪", "base": "USD", "quote": "KES", "otc": False},
    "USDZAR":    {"name": "USD/ZAR",     "flag": "🇺🇸🇿🇦", "base": "USD", "quote": "ZAR", "otc": False},
    "USDINR":    {"name": "USD/INR",     "flag": "🇺🇸🇮🇳", "base": "USD", "quote": "INR", "otc": False},
    "USDSGD":    {"name": "USD/SGD",     "flag": "🇺🇸🇸🇬", "base": "USD", "quote": "SGD", "otc": False},
    "USDMXN":    {"name": "USD/MXN",     "flag": "🇺🇸🇲🇽", "base": "USD", "quote": "MXN", "otc": False},
    "USDMYR":    {"name": "USD/MYR",     "flag": "🇺🇸🇲🇾", "base": "USD", "quote": "MYR", "otc": False},
    "USDTHB":    {"name": "USD/THB",     "flag": "🇺🇸🇹🇭", "base": "USD", "quote": "THB", "otc": False},
    "USDIDR":    {"name": "USD/IDR",     "flag": "🇺🇸🇮🇩", "base": "USD", "quote": "IDR", "otc": False},
    "USDPHP":    {"name": "USD/PHP",     "flag": "🇺🇸🇵🇭", "base": "USD", "quote": "PHP", "otc": False},
    "USDEGP":    {"name": "USD/EGP",     "flag": "🇺🇸🇪🇬", "base": "USD", "quote": "EGP", "otc": False},
    "USDPKR":    {"name": "USD/PKR",     "flag": "🇺🇸🇵🇰", "base": "USD", "quote": "PKR", "otc": False},
    "USDVND":    {"name": "USD/VND",     "flag": "🇺🇸🇻🇳", "base": "USD", "quote": "VND", "otc": False},
    "USDARS":    {"name": "USD/ARS",     "flag": "🇺🇸🇦🇷", "base": "USD", "quote": "ARS", "otc": False},
    "USDCLP":    {"name": "USD/CLP",     "flag": "🇺🇸🇨🇱", "base": "USD", "quote": "CLP", "otc": False},
    "USDCOP":    {"name": "USD/COP",     "flag": "🇺🇸🇨🇴", "base": "USD", "quote": "COP", "otc": False},
    "USDBDT":    {"name": "USD/BDT",     "flag": "🇺🇸🇧🇩", "base": "USD", "quote": "BDT", "otc": False},
    "USDDZD":    {"name": "USD/DZD",     "flag": "🇺🇸🇩🇿", "base": "USD", "quote": "DZD", "otc": False},
}

# ─── INDICES  (Twelve Data) ───────────────────────────────────────────────────
INDICES_PAIRS = {
    "SPX":     {"name": "SP500  (S&P 500)",      "flag": "🇺🇸📈", "otc": False},
    "NDX":     {"name": "US100  (NASDAQ-100)",    "flag": "🇺🇸💻", "otc": False},
    "DJI":     {"name": "DJI30  (Dow Jones)",     "flag": "🇺🇸🏭", "otc": False},
    "FTSE":    {"name": "100GBP (FTSE 100)",      "flag": "🇬🇧📊", "otc": False},
    "DAX":     {"name": "D30EUR (DAX 30)",        "flag": "🇩🇪📊", "otc": False},
    "CAC":     {"name": "F40EUR (CAC 40)",        "flag": "🇫🇷📊", "otc": False},
    "N225":    {"name": "JPN225 (Nikkei 225)",    "flag": "🇯🇵📊", "otc": False},
    "ASX200":  {"name": "AUS200 (ASX 200)",       "flag": "🇦🇺📊", "otc": False},
    "HSI":     {"name": "HK33   (Hang Seng)",     "flag": "🇭🇰📊", "otc": False},
    "STOXX50E":{"name": "E50EUR (EuroStoxx 50)",  "flag": "🇪🇺📊", "otc": False},
    # OTC indices
    "SPXOTC":  {"name": "SP500 OTC",             "flag": "🇺🇸📈", "otc": True},
    "NDXOTC":  {"name": "US100 OTC",             "flag": "🇺🇸💻", "otc": True},
    "DJIОТС":  {"name": "DJI30 OTC",             "flag": "🇺🇸🏭", "otc": True},
    "FTSЕOTC": {"name": "100GBP OTC",            "flag": "🇬🇧📊", "otc": True},
    "DAXOTC":  {"name": "D30EUR OTC",            "flag": "🇩🇪📊", "otc": True},
    "CACOTC":  {"name": "F40EUR OTC",            "flag": "🇫🇷📊", "otc": True},
    "N225OTC": {"name": "JPN225 OTC",            "flag": "🇯🇵📊", "otc": True},
}

# Mapping: OTC index symbol → real Twelve Data symbol for price fetching
INDICES_OTC_MAP = {
    "SPXOTC":  "SPX",
    "NDXOTC":  "NDX",
    "DJIОТС":  "DJI",
    "FTSЕOTC": "FTSE",
    "DAXOTC":  "DAX",
    "CACOTC":  "CAC",
    "N225OTC": "N225",
}

# ─── COMMODITIES  (Twelve Data) ──────────────────────────────────────────────
COMMODITIES_PAIRS = {
    "XAU/USD":   {"name": "Gold (XAU)",        "flag": "🥇", "otc": False},
    "XAG/USD":   {"name": "Silver (XAG)",      "flag": "🥈", "otc": False},
    "WTI/USD":   {"name": "WTI Crude Oil",     "flag": "🛢️", "otc": False},
    "BRENT/USD": {"name": "Brent Crude Oil",   "flag": "🛢️", "otc": False},
    "NATGAS/USD":{"name": "Natural Gas",       "flag": "⛽", "otc": False},
    "XPT/USD":   {"name": "Platinum",          "flag": "⬜", "otc": False},
    "XPD/USD":   {"name": "Palladium",         "flag": "🔳", "otc": False},
    # OTC commodities
    "GOLDOTC":   {"name": "Gold OTC",          "flag": "🥇", "otc": True},
    "SILVEROTC": {"name": "Silver OTC",        "flag": "🥈", "otc": True},
    "WTIOTC":    {"name": "WTI Crude Oil OTC", "flag": "🛢️", "otc": True},
    "BRENTOTC":  {"name": "Brent Oil OTC",     "flag": "🛢️", "otc": True},
    "NATGASOTC": {"name": "Natural Gas OTC",   "flag": "⛽", "otc": True},
    "PLATОTC":   {"name": "Platinum OTC",      "flag": "⬜", "otc": True},
    "PALLOTC":   {"name": "Palladium OTC",     "flag": "🔳", "otc": True},
}

# Mapping: OTC commodity symbol → real Twelve Data symbol
COMMODITIES_OTC_MAP = {
    "GOLDOTC":   "XAU/USD",
    "SILVEROTC": "XAG/USD",
    "WTIOTC":    "WTI/USD",
    "BRENTOTC":  "BRENT/USD",
    "NATGASOTC": "NATGAS/USD",
    "PLATОTC":   "XPT/USD",
    "PALLOTC":   "XPD/USD",
}

# ─── STOCKS  (Twelve Data) ───────────────────────────────────────────────────
STOCKS_PAIRS = {
    # Regular
    "AAPL":  {"name": "Apple",                 "flag": "🍎",  "otc": False},
    "MSFT":  {"name": "Microsoft",             "flag": "🪟",  "otc": False},
    "GOOGL": {"name": "Alphabet / Google",     "flag": "🔍",  "otc": False},
    "AMZN":  {"name": "Amazon",                "flag": "📦",  "otc": False},
    "TSLA":  {"name": "Tesla",                 "flag": "⚡",  "otc": False},
    "NVDA":  {"name": "NVIDIA",                "flag": "🟩",  "otc": False},
    "META":  {"name": "Meta / Facebook",       "flag": "📘",  "otc": False},
    "JPM":   {"name": "JPMorgan Chase",        "flag": "🏛️",  "otc": False},
    "NFLX":  {"name": "Netflix",               "flag": "🎬",  "otc": False},
    "AMD":   {"name": "AMD",                   "flag": "🔴",  "otc": False},
    "INTC":  {"name": "Intel",                 "flag": "🔲",  "otc": False},
    "BABA":  {"name": "Alibaba",               "flag": "🛍️",  "otc": False},
    "XOM":   {"name": "ExxonMobil",            "flag": "🛢️",  "otc": False},
    "V":     {"name": "VISA",                  "flag": "💳",  "otc": False},
    "BA":    {"name": "Boeing",                "flag": "✈️",  "otc": False},
    "CSCO":  {"name": "Cisco",                 "flag": "🔌",  "otc": False},
    "JNJ":   {"name": "Johnson & Johnson",     "flag": "💊",  "otc": False},
    "MCD":   {"name": "McDonald's",            "flag": "🍔",  "otc": False},
    "PFE":   {"name": "Pfizer",                "flag": "💉",  "otc": False},
    "C":     {"name": "Citigroup",             "flag": "🏦",  "otc": False},
    "AXP":   {"name": "American Express",      "flag": "💳",  "otc": False},
    "COIN":  {"name": "Coinbase",              "flag": "🪙",  "otc": False},
    "PLTR":  {"name": "Palantir",              "flag": "🔭",  "otc": False},
    "GME":   {"name": "GameStop",              "flag": "🎮",  "otc": False},
    "FDX":   {"name": "FedEx",                 "flag": "🚚",  "otc": False},
    "MARA":  {"name": "Marathon Digital",      "flag": "⛏️",  "otc": False},
    # OTC stocks (92% payout on Pocket Option)
    "AAPLOTC": {"name": "Apple OTC",           "flag": "🍎",  "otc": True},
    "MSFTOTC": {"name": "Microsoft OTC",       "flag": "🪟",  "otc": True},
    "TSLAOTC": {"name": "Tesla OTC",           "flag": "⚡",  "otc": True},
    "NVDAOTC": {"name": "NVIDIA OTC",          "flag": "🟩",  "otc": True},
    "METAOTC": {"name": "Meta OTC",            "flag": "📘",  "otc": True},
    "AMZNOTC": {"name": "Amazon OTC",          "flag": "📦",  "otc": True},
    "NFLXOTC": {"name": "Netflix OTC",         "flag": "🎬",  "otc": True},
    "AMDOTC":  {"name": "AMD OTC",             "flag": "🔴",  "otc": True},
    "INTCOTC": {"name": "Intel OTC",           "flag": "🔲",  "otc": True},
    "XOMOTC":  {"name": "ExxonMobil OTC",      "flag": "🛢️",  "otc": True},
    "MCДOTC":  {"name": "McDonald's OTC",      "flag": "🍔",  "otc": True},
    "PFЕOTC":  {"name": "Pfizer OTC",          "flag": "💉",  "otc": True},
    "COTC":    {"name": "Citigroup OTC",       "flag": "🏦",  "otc": True},
    "VOTC":    {"name": "VISA OTC",            "flag": "💳",  "otc": True},
    "BAOTC":   {"name": "Boeing OTC",          "flag": "✈️",  "otc": True},
    "COINOTC": {"name": "Coinbase OTC",        "flag": "🪙",  "otc": True},
    "PLТROTC": {"name": "Palantir OTC",        "flag": "🔭",  "otc": True},
    "GMEOTC":  {"name": "GameStop OTC",        "flag": "🎮",  "otc": True},
    "BABAOTC": {"name": "Alibaba OTC",         "flag": "🛍️",  "otc": True},
}

# Mapping: OTC stock symbol → real Twelve Data symbol
STOCKS_OTC_MAP = {
    "AAPLOTC": "AAPL", "MSFTOTC": "MSFT", "TSLAOTC": "TSLA",
    "NVDAOTC": "NVDA", "METAOTC": "META", "AMZNOTC": "AMZN",
    "NFLXOTC": "NFLX", "AMDOTC":  "AMD",  "INTCOTC": "INTC",
    "XOMOTC":  "XOM",  "MCДOTC":  "MCD",  "PFЕOTC":  "PFE",
    "COTC":    "C",    "VOTC":    "V",    "BAOTC":   "BA",
    "COINOTC": "COIN", "PLТROTC": "PLTR", "GMEOTC":  "GME",
    "BABAOTC": "BABA",
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
    """
    For OTC pairs, return the real underlying symbol used for price fetching.
    For regular pairs, return the symbol unchanged.
    """
    if category == "indices":
        return INDICES_OTC_MAP.get(symbol, symbol)
    elif category == "commodities":
        return COMMODITIES_OTC_MAP.get(symbol, symbol)
    elif category == "stocks":
        return STOCKS_OTC_MAP.get(symbol, symbol)
    elif category == "crypto":
        # OTC crypto shares same cg_id as base symbol via pair_info
        return symbol
    elif category == "forex":
        return symbol  # forex OTC uses same base/quote
    return symbol
