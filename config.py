"""
Configuration settings for the Forex Signal Bot - COMPLETE EDITION
"""

# ============================================
# COMPLETE FOREX PAIRS - ALL MAJOR, MINOR, EXOTIC
# ============================================

# MAJOR PAIRS (Most Liquid)
MAJOR_PAIRS = [
    "EURUSD",   # Euro / US Dollar
    "GBPUSD",   # British Pound / US Dollar  
    "USDJPY",   # US Dollar / Japanese Yen
    "AUDUSD",   # Australian Dollar / US Dollar
    "USDCAD",   # US Dollar / Canadian Dollar
    "NZDUSD",   # New Zealand Dollar / US Dollar
    "USDCHF",   # US Dollar / Swiss Franc
]

# MINOR PAIRS (Crosses)
MINOR_PAIRS = [
    "EURGBP",   # Euro / British Pound
    "EURJPY",   # Euro / Japanese Yen
    "EURCHF",   # Euro / Swiss Franc
    "EURCAD",   # Euro / Canadian Dollar
    "EURAUD",   # Euro / Australian Dollar
    "EURNZD",   # Euro / New Zealand Dollar
    "GBPJPY",   # British Pound / Japanese Yen
    "GBPCHF",   # British Pound / Swiss Franc
    "GBPCAD",   # British Pound / Canadian Dollar
    "GBPAUD",   # British Pound / Australian Dollar
    "GBPNZD",   # British Pound / New Zealand Dollar
    "AUDJPY",   # Australian Dollar / Japanese Yen
    "AUDCHF",   # Australian Dollar / Swiss Franc
    "AUDCAD",   # Australian Dollar / Canadian Dollar
    "AUDNZD",   # Australian Dollar / New Zealand Dollar
    "CADJPY",   # Canadian Dollar / Japanese Yen
    "CADCHF",   # Canadian Dollar / Swiss Franc
    "NZDJPY",   # New Zealand Dollar / Japanese Yen
    "NZDCHF",   # New Zealand Dollar / Swiss Franc
    "CHFJPY",   # Swiss Franc / Japanese Yen
]

# EXOTIC PAIRS
EXOTIC_PAIRS = [
    "USDTRY",   # US Dollar / Turkish Lira
    "USDZAR",   # US Dollar / South African Rand
    "USDMXN",   # US Dollar / Mexican Peso
    "USDSGD",   # US Dollar / Singapore Dollar
    "USDHKD",   # US Dollar / Hong Kong Dollar
    "USDDKK",   # US Dollar / Danish Krone
    "USDNOK",   # US Dollar / Norwegian Krone
    "USDSEK",   # US Dollar / Swedish Krona
    "USDPLN",   # US Dollar / Polish Zloty
    "USDCNY",   # US Dollar / Chinese Yuan
    "USDRUB",   # US Dollar / Russian Ruble
    "USDBRL",   # US Dollar / Brazilian Real
    "USDINR",   # US Dollar / Indian Rupee
    "USDKRW",   # US Dollar / South Korean Won
    "USDTHB",   # US Dollar / Thai Baht
    "USDIDR",   # US Dollar / Indonesian Rupiah
    "EURTRY",   # Euro / Turkish Lira
    "EURZAR",   # Euro / South African Rand
    "EURMXN",   # Euro / Mexican Peso
    "GBPZAR",   # British Pound / South African Rand
    "GBPTRY",   # British Pound / Turkish Lira
    "AUDTRY",   # Australian Dollar / Turkish Lira
    "CADTRY",   # Canadian Dollar / Turkish Lira
]

# COMMODITY PAIRS
COMMODITY_PAIRS = [
    "XAUUSD",   # Gold / US Dollar
    "XAGUSD",   # Silver / US Dollar
    "XAUAUD",   # Gold / Australian Dollar
    "XAUEUR",   # Gold / Euro
    "XAUGBP",   # Gold / British Pound
    "XAUJPY",   # Gold / Japanese Yen
    "XPDUSD",   # Palladium / US Dollar
    "XPTUSD",   # Platinum / US Dollar
    "USOIL",    # US Oil
    "UKOIL",    # UK Oil
    "BRENT",    # Brent Oil
]

# CRYPTO PAIRS (if your broker supports)
CRYPTO_PAIRS = [
    "BTCUSD",   # Bitcoin / US Dollar
    "ETHUSD",   # Ethereum / US Dollar
    "LTCUSD",   # Litecoin / US Dollar
    "XRPUSD",   # Ripple / US Dollar
    "BNBUSD",   # Binance Coin / US Dollar
    "ADAUSD",   # Cardano / US Dollar
    "DOTUSD",   # Polkadot / US Dollar
    "DOGEUSD",  # Dogecoin / US Dollar
    "SOLUSD",   # Solana / US Dollar
    "MATICUSD", # Polygon / US Dollar
]

# Combine ALL pairs (you can choose which groups to include)
ALL_FOREX_PAIRS = MAJOR_PAIRS + MINOR_PAIRS + EXOTIC_PAIRS + COMMODITY_PAIRS

# Optional: Include crypto if supported
# ALL_FOREX_PAIRS = MAJOR_PAIRS + MINOR_PAIRS + EXOTIC_PAIRS + COMMODITY_PAIRS + CRYPTO_PAIRS

# ============================================
# SELECT WHICH PAIRS TO MONITOR
# ============================================

# Option 1: All pairs (slower but comprehensive)
FOREX_PAIRS = ALL_FOREX_PAIRS

# Option 2: Only majors and minors (faster)
# FOREX_PAIRS = MAJOR_PAIRS + MINOR_PAIRS

# Option 3: Only majors (fastest)
# FOREX_PAIRS = MAJOR_PAIRS

# Option 4: Custom selection
# FOREX_PAIRS = [
#     "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"
# ]

# ============================================
# FLAGS FOR ALL PAIRS
# ============================================

FLAGS = {
    # Majors
    "EURUSD": "🇪🇺🇺🇸",
    "GBPUSD": "🇬🇧🇺🇸",
    "USDJPY": "🇺🇸🇯🇵",
    "AUDUSD": "🇦🇺🇺🇸",
    "USDCAD": "🇺🇸🇨🇦",
    "NZDUSD": "🇳🇿🇺🇸",
    "USDCHF": "🇺🇸🇨🇭",
    
    # Minors
    "EURGBP": "🇪🇺🇬🇧",
    "EURJPY": "🇪🇺🇯🇵",
    "EURCHF": "🇪🇺🇨🇭",
    "EURCAD": "🇪🇺🇨🇦",
    "EURAUD": "🇪🇺🇦🇺",
    "EURNZD": "🇪🇺🇳🇿",
    "GBPJPY": "🇬🇧🇯🇵",
    "GBPCHF": "🇬🇧🇨🇭",
    "GBPCAD": "🇬🇧🇨🇦",
    "GBPAUD": "🇬🇧🇦🇺",
    "GBPNZD": "🇬🇧🇳🇿",
    "AUDJPY": "🇦🇺🇯🇵",
    "AUDCHF": "🇦🇺🇨🇭",
    "AUDCAD": "🇦🇺🇨🇦",
    "AUDNZD": "🇦🇺🇳🇿",
    "CADJPY": "🇨🇦🇯🇵",
    "CADCHF": "🇨🇦🇨🇭",
    "NZDJPY": "🇳🇿🇯🇵",
    "NZDCHF": "🇳🇿🇨🇭",
    "CHFJPY": "🇨🇭🇯🇵",
    
    # Exotics
    "USDTRY": "🇺🇸🇹🇷",
    "USDZAR": "🇺🇸🇿🇦",
    "USDMXN": "🇺🇸🇲🇽",
    "USDSGD": "🇺🇸🇸🇬",
    "USDHKD": "🇺🇸🇭🇰",
    "USDNOK": "🇺🇸🇳🇴",
    "USDSEK": "🇺🇸🇸🇪",
    "USDPLN": "🇺🇸🇵🇱",
    "USDCNY": "🇺🇸🇨🇳",
    "USDRUB": "🇺🇸🇷🇺",
    "USDBRL": "🇺🇸🇧🇷",
    "USDINR": "🇺🇸🇮🇳",
    
    # Commodities
    "XAUUSD": "🥇🇺🇸",
    "XAGUSD": "🥈🇺🇸",
    "XAUAUD": "🥇🇦🇺",
    "XAUEUR": "🥇🇪🇺",
    "XAUGBP": "🥇🇬🇧",
    "XAUJPY": "🥇🇯🇵",
    "USOIL": "🛢️🇺🇸",
    "UKOIL": "🛢️🇬🇧",
    "BRENT": "🛢️🌍",
    
    # Crypto
    "BTCUSD": "₿🇺🇸",
    "ETHUSD": "⟠🇺🇸",
    "LTCUSD": "Ł🇺🇸",
    "XRPUSD": "✖️🇺🇸",
    "BNBUSD": "🟡🇺🇸",
    "ADAUSD": "🟣🇺🇸",
    "DOGEUSD": "🐕🇺🇸",
    "SOLUSD": "⚡🇺🇸",
}

# ============================================
# REST OF YOUR CONFIGURATION
# ============================================

# Timeframes to analyze
TIMEFRAMES = {
    "1min": "1min",
    "5min": "5min",
    "15min": "15min",
    "30min": "30min",
}

# Technical Indicator Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_STD = 2

MA_FAST = 9
MA_MEDIUM = 21
MA_SLOW = 50

STOCH_RSI_PERIOD = 14
STOCH_RSI_K = 3
STOCH_RSI_D = 3

ATR_PERIOD = 14

# Trading Strategies Weights
STRATEGIES = {
    "RSI_DIVERGENCE": 25,
    "MACD_CROSSOVER": 25,
    "BOLLINGER_SQUEEZE": 20,
    "MA_CROSSOVER": 20,
    "STOCH_RSI": 15,
    "FIBO_RETRACEMENT": 15,
    "SUPPORT_RESISTANCE": 20,
    "CANDLE_PATTERNS": 15,
    "VOLUME_SPIKE": 10,
}

# Minimum confidence to generate signal
MIN_CONFIDENCE = 40

# Signal strength levels
SIGNAL_STRENGTH = {
    "WEAK": 40,
    "MEDIUM": 60,
    "STRONG": 75,
    "VERY_STRONG": 90
}

# Martingale Settings
MARTINGALE_LEVELS = 3
MARTINGALE_MULTIPLIER = 2.0
MARTINGALE_INTERVAL_MINUTES = 3

# Scan interval (minutes)
SCAN_INTERVAL_MINUTES = 5

# Direction emojis
DIRECTION_EMOJIS = {
    "BUY": "🟩",
    "SELL": "🟥",
    "STRONG_BUY": "🟢🟢",
    "STRONG_SELL": "🔴🔴"
}

# Timeframes to analyze
TIMEFRAMES = {
    "5min": "5min",
    "15min": "15min",
    "30min": "30min", 
    "1hour": "60min",
    "daily": "daily",
}

# RSI Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# EMA Settings
EMA_FAST = 9
EMA_SLOW = 21

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Signal weights
WEIGHTS = {
    "RSI_EXTREME": 30,
    "RSI_CROSSOVER": 20,
    "EMA_ALIGNMENT": 30,
    "EMA_CROSSOVER": 25,
    "MACD_ALIGNMENT": 30,
    "MACD_CROSSOVER": 25,
    "SUPPORT_RESISTANCE": 10,
}

# Minimum confidence for signals
MIN_CONFIDENCE = 20

# Scan interval in minutes
SCAN_INTERVAL_MINUTES = 5

# Signal emojis
SIGNAL_EMOJIS = {
    "STRONG_BUY": "🟢🟢",
    "BUY": "🟢",
    "NEUTRAL": "⚪",
    "SELL": "🔴",
    "STRONG_SELL": "🔴🔴",
}

# ============================================
# SELECT YOUR SCANNING MODE
# ============================================

# MODE 1: ALL PAIRS (100+ pairs) - Comprehensive but slower
# FOREX_PAIRS = ALL_FOREX_PAIRS

# MODE 2: MAJORS + MINORS + COMMODITIES (50+ pairs) - Recommended
FOREX_PAIRS = MAJOR_PAIRS + MINOR_PAIRS + COMMODITY_PAIRS

# MODE 3: MAJORS ONLY (7 pairs) - Fastest
# FOREX_PAIRS = MAJOR_PAIRS

# MODE 4: CUSTOM SELECTION
# FOREX_PAIRS = [
#     "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD",
#     "EURGBP", "GBPJPY", "USDCAD", "AUDUSD", "NZDUSD"
# ]
