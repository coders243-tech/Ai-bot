# config.py
# Central configuration for Forex Crypto Signal Bot v2

# ─── RSI SETTINGS ────────────────────────────────────────────────────────────
RSI_PERIOD        = 14    # RSI lookback period
RSI_OVERSOLD      = 35    # BUY threshold  (raised from 30 → more signals)
RSI_OVERBOUGHT    = 65    # SELL threshold (lowered from 70 → more signals)
MIN_PRICE_HISTORY = 15    # Minimum data points before RSI is calculated

# ─── SCAN / SIGNAL SETTINGS ──────────────────────────────────────────────────
SCAN_INTERVAL_MIN   = 10    # minutes (lower bound of random scan interval)
SCAN_INTERVAL_MAX   = 12    # minutes (upper bound)
COOLDOWN_SECONDS    = 300   # 5-minute cooldown per pair (was 10 min)
TRADE_DURATION_DEFAULT = 5  # default trade duration in minutes
CONFIDENCE_DEFAULT  = 50    # default minimum confidence % to send signal
MARTINGALE_LEVELS   = 3     # martingale steps
MARTINGALE_GAP_MIN  = 3     # minutes between martingale levels
TP_SL_PCT           = 0.005 # 0.5% take-profit / stop-loss

# ─── TIMEZONE ────────────────────────────────────────────────────────────────
TIMEZONE_NAME   = "WAT"     # West Africa Time
TIMEZONE_OFFSET = 1         # UTC+1

# ─── CRYPTO PAIRS (fetched via CoinGecko) ────────────────────────────────────
# symbol → { name, flag, coingecko_id }
CRYPTO_PAIRS = {
    "BTCUSDT":   {"name": "Bitcoin/USDT",       "flag": "🟡",  "cg_id": "bitcoin"},
    "ETHUSDT":   {"name": "Ethereum/USDT",      "flag": "🔷",  "cg_id": "ethereum"},
    "BNBUSDT":   {"name": "BNB/USDT",           "flag": "🟨",  "cg_id": "binancecoin"},
    "SOLUSDT":   {"name": "Solana/USDT",        "flag": "🟣",  "cg_id": "solana"},
    "XRPUSDT":   {"name": "Ripple/USDT",        "flag": "🔵",  "cg_id": "ripple"},
    "ADAUSDT":   {"name": "Cardano/USDT",       "flag": "💙",  "cg_id": "cardano"},
    "DOGEUSDT":  {"name": "Dogecoin/USDT",      "flag": "🐶",  "cg_id": "dogecoin"},
    "AVAXUSDT":  {"name": "Avalanche/USDT",     "flag": "🔺",  "cg_id": "avalanche-2"},
    "DOTUSDT":   {"name": "Polkadot/USDT",      "flag": "⚫",  "cg_id": "polkadot"},
    "MATICUSDT": {"name": "Polygon/USDT",       "flag": "🟪",  "cg_id": "matic-network"},
    "LINKUSDT":  {"name": "Chainlink/USDT",     "flag": "🔗",  "cg_id": "chainlink"},
    "LTCUSDT":   {"name": "Litecoin/USDT",      "flag": "⚪",  "cg_id": "litecoin"},
    "UNIUSDT":   {"name": "Uniswap/USDT",       "flag": "🦄",  "cg_id": "uniswap"},
    "ATOMUSDT":  {"name": "Cosmos/USDT",        "flag": "⚛️",  "cg_id": "cosmos"},
    "NEARUSDT":  {"name": "NEAR Protocol/USDT", "flag": "🌐",  "cg_id": "near"},
    "AAVEUSDT":  {"name": "Aave/USDT",          "flag": "👻",  "cg_id": "aave"},
    "FTMUSDT":   {"name": "Fantom/USDT",        "flag": "👁️",  "cg_id": "fantom"},
    "ALGOUSDT":  {"name": "Algorand/USDT",      "flag": "🔘",  "cg_id": "algorand"},
    "XLMUSDT":   {"name": "Stellar/USDT",       "flag": "✨",  "cg_id": "stellar"},
    "VETUSDT":   {"name": "VeChain/USDT",       "flag": "☑️",  "cg_id": "vechain"},
}

# ─── FOREX PAIRS (Alpha Vantage CURRENCY_EXCHANGE_RATE) ──────────────────────
FOREX_PAIRS = {
    "EURUSD": {"name": "Euro / US Dollar",          "flag": "🇪🇺🇺🇸", "from": "EUR", "to": "USD"},
    "GBPUSD": {"name": "Pound / US Dollar",         "flag": "🇬🇧🇺🇸", "from": "GBP", "to": "USD"},
    "USDJPY": {"name": "US Dollar / Yen",           "flag": "🇺🇸🇯🇵", "from": "USD", "to": "JPY"},
    "USDCHF": {"name": "US Dollar / Swiss Franc",   "flag": "🇺🇸🇨🇭", "from": "USD", "to": "CHF"},
    "AUDUSD": {"name": "Aussie / US Dollar",        "flag": "🇦🇺🇺🇸", "from": "AUD", "to": "USD"},
    "USDCAD": {"name": "US Dollar / CAD",           "flag": "🇺🇸🇨🇦", "from": "USD", "to": "CAD"},
    "NZDUSD": {"name": "NZD / US Dollar",           "flag": "🇳🇿🇺🇸", "from": "NZD", "to": "USD"},
    "EURGBP": {"name": "Euro / Pound",              "flag": "🇪🇺🇬🇧", "from": "EUR", "to": "GBP"},
    "GBPJPY": {"name": "Pound / Yen",               "flag": "🇬🇧🇯🇵", "from": "GBP", "to": "JPY"},
    "EURJPY": {"name": "Euro / Yen",                "flag": "🇪🇺🇯🇵", "from": "EUR", "to": "JPY"},
    "USDNGN": {"name": "US Dollar / Naira",         "flag": "🇺🇸🇳🇬", "from": "USD", "to": "NGN"},
    "GBPNGN": {"name": "Pound / Naira",             "flag": "🇬🇧🇳🇬", "from": "GBP", "to": "NGN"},
    "EURNGN": {"name": "Euro / Naira",              "flag": "🇪🇺🇳🇬", "from": "EUR", "to": "NGN"},
    "USDZAR": {"name": "US Dollar / Rand",          "flag": "🇺🇸🇿🇦", "from": "USD", "to": "ZAR"},
    "USDGHS": {"name": "US Dollar / Ghanaian Cedi", "flag": "🇺🇸🇬🇭", "from": "USD", "to": "GHS"},
    "USDKES": {"name": "US Dollar / Kenyan Shilling","flag": "🇺🇸🇰🇪","from": "USD", "to": "KES"},
    "EURCAD": {"name": "Euro / CAD",                "flag": "🇪🇺🇨🇦", "from": "EUR", "to": "CAD"},
    "CHFJPY": {"name": "Swiss Franc / Yen",         "flag": "🇨🇭🇯🇵", "from": "CHF", "to": "JPY"},
    "AUDCAD": {"name": "Aussie / CAD",              "flag": "🇦🇺🇨🇦", "from": "AUD", "to": "CAD"},
    "GBPAUD": {"name": "Pound / Aussie",            "flag": "🇬🇧🇦🇺", "from": "GBP", "to": "AUD"},
}

# ─── INDICES (Alpha Vantage GLOBAL_QUOTE via ETF proxies) ────────────────────
INDICES_PAIRS = {
    "SPY":  {"name": "S&P 500 ETF",         "flag": "🇺🇸📈"},
    "QQQ":  {"name": "NASDAQ-100 ETF",      "flag": "🇺🇸💻"},
    "DIA":  {"name": "Dow Jones ETF",       "flag": "🇺🇸🏭"},
    "IWM":  {"name": "Russell 2000 ETF",    "flag": "🇺🇸🔬"},
    "EWJ":  {"name": "Japan Nikkei ETF",    "flag": "🇯🇵📊"},
    "EWG":  {"name": "Germany DAX ETF",     "flag": "🇩🇪📊"},
    "EWU":  {"name": "UK FTSE ETF",         "flag": "🇬🇧📊"},
    "EWZ":  {"name": "Brazil Index ETF",    "flag": "🇧🇷📊"},
    "FXI":  {"name": "China Large-Cap ETF", "flag": "🇨🇳📊"},
    "EWY":  {"name": "South Korea ETF",     "flag": "🇰🇷📊"},
    "EWA":  {"name": "Australia ETF",       "flag": "🇦🇺📊"},
    "EZA":  {"name": "South Africa ETF",    "flag": "🇿🇦📊"},
}

# ─── COMMODITIES (Alpha Vantage GLOBAL_QUOTE via ETF proxies) ────────────────
COMMODITIES_PAIRS = {
    "GLD":  {"name": "Gold ETF",              "flag": "🥇"},
    "SLV":  {"name": "Silver ETF",            "flag": "🥈"},
    "USO":  {"name": "Crude Oil ETF",         "flag": "🛢️"},
    "UNG":  {"name": "Natural Gas ETF",       "flag": "⛽"},
    "PDBC": {"name": "Diversified Commodity", "flag": "📦"},
    "CORN": {"name": "Corn ETF",              "flag": "🌽"},
    "WEAT": {"name": "Wheat ETF",             "flag": "🌾"},
    "CPER": {"name": "Copper ETF",            "flag": "🟤"},
    "PPLT": {"name": "Platinum ETF",          "flag": "⬜"},
    "PALL": {"name": "Palladium ETF",         "flag": "🔳"},
}

# ─── STOCKS (Alpha Vantage GLOBAL_QUOTE) ─────────────────────────────────────
STOCKS_PAIRS = {
    "AAPL":  {"name": "Apple Inc.",           "flag": "🍎"},
    "MSFT":  {"name": "Microsoft Corp.",      "flag": "🪟"},
    "GOOGL": {"name": "Alphabet Inc.",        "flag": "🔍"},
    "AMZN":  {"name": "Amazon.com Inc.",      "flag": "📦"},
    "TSLA":  {"name": "Tesla Inc.",           "flag": "⚡"},
    "NVDA":  {"name": "NVIDIA Corp.",         "flag": "🎮"},
    "META":  {"name": "Meta Platforms",       "flag": "📘"},
    "JPM":   {"name": "JPMorgan Chase",       "flag": "🏦"},
    "XOM":   {"name": "ExxonMobil Corp.",     "flag": "🛢️"},
    "V":     {"name": "Visa Inc.",            "flag": "💳"},
    "WMT":   {"name": "Walmart Inc.",         "flag": "🛒"},
    "JNJ":   {"name": "Johnson & Johnson",    "flag": "💊"},
    "BAC":   {"name": "Bank of America",      "flag": "🏛️"},
    "DIS":   {"name": "Walt Disney Co.",      "flag": "🏰"},
    "NFLX":  {"name": "Netflix Inc.",         "flag": "🎬"},
    "PYPL":  {"name": "PayPal Holdings",      "flag": "💰"},
    "INTC":  {"name": "Intel Corp.",          "flag": "🔲"},
    "AMD":   {"name": "Advanced Micro Dev.",  "flag": "🔴"},
    "UBER":  {"name": "Uber Technologies",    "flag": "🚗"},
    "COIN":  {"name": "Coinbase Global",      "flag": "🪙"},
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
    """Return flat list of (category, symbol) tuples."""
    result = []
    for cat, pairs in get_all_pairs().items():
        for sym in pairs:
            result.append((cat, sym))
    return result
