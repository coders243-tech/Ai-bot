# config.py
# Central configuration for Forex Crypto Signal Bot
# Pairs, emojis, RSI parameters, and scan settings

# ─── RSI SETTINGS ────────────────────────────────────────────────────────────
RSI_PERIOD = 14            # Standard RSI lookback period
RSI_OVERSOLD = 30          # BUY threshold
RSI_OVERBOUGHT = 70        # SELL threshold
MIN_PRICE_HISTORY = 15     # Minimum data points before RSI is valid

# ─── SCAN / SIGNAL SETTINGS ──────────────────────────────────────────────────
SCAN_INTERVAL_MIN = 10     # seconds between full scans (base)
SCAN_INTERVAL_MAX = 12     # jitter ceiling (seconds added randomly)
COOLDOWN_SECONDS = 600     # 10-minute cooldown per pair
TRADE_DURATION_DEFAULT = 5 # default trade duration in minutes
CONFIDENCE_DEFAULT = 55    # default minimum confidence to send a signal (%)
MARTINGALE_LEVELS = 3      # number of martingale steps
MARTINGALE_GAP_MIN = 3     # minutes between martingale levels
TP_SL_PCT = 0.005          # 0.5% take-profit / stop-loss from entry

# ─── TIMEZONE ─────────────────────────────────────────────────────────────────
TIMEZONE_NAME = "WAT"      # West Africa Time
TIMEZONE_OFFSET = 1        # UTC+1

# ─── CRYPTOCURRENCY PAIRS (Binance symbols) ───────────────────────────────────
# 12 major/popular coins against USDT
CRYPTO_PAIRS = {
    "BTCUSDT":  {"name": "Bitcoin/USDT",      "flag": "🟡"},
    "ETHUSDT":  {"name": "Ethereum/USDT",     "flag": "🔷"},
    "BNBUSDT":  {"name": "BNB/USDT",          "flag": "🟨"},
    "SOLUSDT":  {"name": "Solana/USDT",       "flag": "🟣"},
    "XRPUSDT":  {"name": "Ripple/USDT",       "flag": "🔵"},
    "ADAUSDT":  {"name": "Cardano/USDT",      "flag": "💙"},
    "DOGEUSDT": {"name": "Dogecoin/USDT",     "flag": "🐶"},
    "AVAXUSDT": {"name": "Avalanche/USDT",    "flag": "🔺"},
    "DOTUSDT":  {"name": "Polkadot/USDT",     "flag": "⚫"},
    "MATICUSDT":{"name": "Polygon/USDT",      "flag": "🟪"},
    "LINKUSDT": {"name": "Chainlink/USDT",    "flag": "🔗"},
    "LTCUSDT":  {"name": "Litecoin/USDT",     "flag": "⚪"},
}

# ─── FOREX PAIRS (Alpha Vantage CURRENCY_EXCHANGE_RATE) ───────────────────────
# from_currency / to_currency format
FOREX_PAIRS = {
    "EURUSD": {"name": "Euro/US Dollar",         "flag": "🇪🇺🇺🇸", "from": "EUR", "to": "USD"},
    "GBPUSD": {"name": "Pound/US Dollar",        "flag": "🇬🇧🇺🇸", "from": "GBP", "to": "USD"},
    "USDJPY": {"name": "US Dollar/Yen",          "flag": "🇺🇸🇯🇵", "from": "USD", "to": "JPY"},
    "USDCHF": {"name": "US Dollar/Swiss Franc",  "flag": "🇺🇸🇨🇭", "from": "USD", "to": "CHF"},
    "AUDUSD": {"name": "Aussie/US Dollar",       "flag": "🇦🇺🇺🇸", "from": "AUD", "to": "USD"},
    "USDCAD": {"name": "US Dollar/CAD",          "flag": "🇺🇸🇨🇦", "from": "USD", "to": "CAD"},
    "NZDUSD": {"name": "NZD/US Dollar",          "flag": "🇳🇿🇺🇸", "from": "NZD", "to": "USD"},
    "EURGBP": {"name": "Euro/Pound",             "flag": "🇪🇺🇬🇧", "from": "EUR", "to": "GBP"},
    "GBPJPY": {"name": "Pound/Yen",              "flag": "🇬🇧🇯🇵", "from": "GBP", "to": "JPY"},
    "EURJPY": {"name": "Euro/Yen",               "flag": "🇪🇺🇯🇵", "from": "EUR", "to": "JPY"},
}

# ─── INDICES (Alpha Vantage GLOBAL_QUOTE) ─────────────────────────────────────
# Uses ETF tickers as proxies (freely available on Alpha Vantage free tier)
INDICES_PAIRS = {
    "SPY":  {"name": "S&P 500 ETF",       "flag": "🇺🇸📈"},
    "QQQ":  {"name": "NASDAQ-100 ETF",    "flag": "🇺🇸💻"},
    "DIA":  {"name": "Dow Jones ETF",     "flag": "🇺🇸🏭"},
    "IWM":  {"name": "Russell 2000 ETF",  "flag": "🇺🇸🔬"},
    "EWJ":  {"name": "Japan Index ETF",   "flag": "🇯🇵📊"},
    "EWG":  {"name": "Germany Index ETF", "flag": "🇩🇪📊"},
    "EWU":  {"name": "UK Index ETF",      "flag": "🇬🇧📊"},
}

# ─── COMMODITIES (Alpha Vantage GLOBAL_QUOTE via ETFs) ────────────────────────
COMMODITIES_PAIRS = {
    "GLD":  {"name": "Gold ETF",          "flag": "🥇"},
    "SLV":  {"name": "Silver ETF",        "flag": "🥈"},
    "USO":  {"name": "Crude Oil ETF",     "flag": "🛢️"},
    "UNG":  {"name": "Natural Gas ETF",   "flag": "⛽"},
    "PDBC": {"name": "Commodities ETF",   "flag": "📦"},
    "CORN": {"name": "Corn ETF",          "flag": "🌽"},
    "WEAT": {"name": "Wheat ETF",         "flag": "🌾"},
}

# ─── STOCKS (Alpha Vantage GLOBAL_QUOTE) ──────────────────────────────────────
STOCKS_PAIRS = {
    "AAPL":  {"name": "Apple Inc.",          "flag": "🍎"},
    "MSFT":  {"name": "Microsoft Corp.",     "flag": "🪟"},
    "GOOGL": {"name": "Alphabet Inc.",       "flag": "🔍"},
    "AMZN":  {"name": "Amazon.com Inc.",     "flag": "📦"},
    "TSLA":  {"name": "Tesla Inc.",          "flag": "⚡"},
    "NVDA":  {"name": "NVIDIA Corp.",        "flag": "🎮"},
    "META":  {"name": "Meta Platforms",      "flag": "📘"},
    "JPM":   {"name": "JPMorgan Chase",      "flag": "🏦"},
    "XOM":   {"name": "ExxonMobil Corp.",    "flag": "⛽"},
    "V":     {"name": "Visa Inc.",           "flag": "💳"},
}

# ─── COMBINED LOOKUP HELPERS ──────────────────────────────────────────────────

def get_all_pairs():
    """Return all pair symbols grouped by category."""
    return {
        "crypto":      CRYPTO_PAIRS,
        "forex":       FOREX_PAIRS,
        "indices":     INDICES_PAIRS,
        "commodities": COMMODITIES_PAIRS,
        "stocks":      STOCKS_PAIRS,
    }

def find_pair(symbol: str):
    """
    Given a symbol string (case-insensitive), return
    (category, symbol_key, pair_info_dict) or (None, None, None).
    """
    sym = symbol.upper()
    for category, pairs in get_all_pairs().items():
        if sym in pairs:
            return category, sym, pairs[sym]
    return None, None, None

def all_symbols_flat():
    """Return a flat list of all (category, symbol) tuples."""
    result = []
    for cat, pairs in get_all_pairs().items():
        for sym in pairs:
            result.append((cat, sym))
    return result