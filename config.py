"""
Configuration settings for Pocket Option Trading Bot
COMPLETE LIST - ALL PAIRS FROM YOUR IMAGES
"""

# ============================================
# FOREX PAIRS (All from your images)
# ============================================

# Majors
MAJOR_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF",
]

# Minor Forex Crosses
MINOR_PAIRS = [
    "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD", "EURNZD",
    "GBPJPY", "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD",
    "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    "NZDJPY", "NZDCHF", "CADJPY", "CADCHF", "CHFJPY",
]

# Exotic Forex (From your images)
EXOTIC_PAIRS = [
    # African currencies
    "USDZAR", "USDNGN", "NGNUSD", "USDKES", "KESUSD", "USDTND", "TNDUSD",
    "USDMAD", "MADUSD", "USDDZD", "USDEGP", "USDLBP", "LBPUSD", "USDZAR",
    # Asian currencies
    "USDSGD", "USDIDR", "USDPHP", "USDTHB", "USDMYR", "USDPKR", "USDBDT",
    "USDINR", "USDCNY", "USDHKD", "USDTWD", "USDKRW", "USDVND",
    # Middle Eastern
    "AEDCNY", "SARCNY", "QARCNY", "OMRCNY", "BHDCNY", "JODCNY", "YERUSD",
    "USDTRY", "USDRUB", "USDILS",
    # Latin American
    "USDMXN", "USDBRL", "USDARS", "USDCLP", "USDCOP", "USDPEN", "USDUYU",
    # European exotics
    "EURTRY", "EURHUF", "EURPLN", "EURCZK", "EURRUB", "EURRON", "EURZAR",
    "GBPZAR", "GBPTRY", "CHFNOK", "CHFSEK", "NOKSEK",
    # Other crosses from your images
    "NGNINR", "NGNCNY", "KESUSD", "UAHUSD", "MADUSD", "FIIRGRP", "NGNUSD",
]

# All Forex combined
FOREX_PAIRS = MAJOR_PAIRS + MINOR_PAIRS + EXOTIC_PAIRS

# OTC Forex (Pocket Option uses _otc suffix)
OTC_FOREX = [f"{pair}_otc" for pair in FOREX_PAIRS]

# ============================================
# INDICES (From your images)
# ============================================

INDICES = [
    "US100", "US30", "US500",           # US indices
    "DJI30", "SP500",                   # Alternative names
    "AEX25", "CAC40",                   # European
    "D30EUR", "E35EUR", "E50EUR", "F40EUR",
    "GER30", "UK100", "FRA40", "ESP35",
    "HONGKONG33", "JPN225",             # Asian
    "AUS200", "100GBP",                 # Australia & UK
    "NIFTY50", "KOSPI", "RUSSIA", "BRAZIL50",
]

INDICES_OTC = [f"{idx}_otc" for idx in INDICES]

# ============================================
# COMMODITIES (From your images)
# ============================================

COMMODITIES = [
    "Gold", "Silver", "Platinum", "Palladium",
    "BrentOil", "WTICrudeOil", "NaturalGas",
    "Copper", "Aluminum", "Zinc", "Lead", "Nickel",
    "Corn", "Wheat", "Soybean", "Coffee", "Sugar", "Cotton",
]

COMMODITIES_OTC = [f"{comm}_otc" for comm in COMMODITIES]

# ============================================
# CRYPTOCURRENCIES (From your images)
# ============================================

CRYPTOS = [
    "Bitcoin", "Ethereum", "Solana", "Cardano", "Dogecoin",
    "Ripple", "Litecoin", "Chainlink", "Avalanche", "Polygon",
    "TRON", "Polkadot", "Uniswap", "Stellar", "Algorand",
    "VeChain", "Theta", "Filecoin", "InternetComputer",
    "ApeCoin", "ShibaInu", "Fantom", "NearProtocol",
]

CRYPTOS_OTC = [f"{crypto}_otc" for crypto in CRYPTOS]

# ============================================
# STOCKS (From your images)
# ============================================

STOCKS = [
    # Tech
    "Apple", "Microsoft", "Google", "Meta", "Amazon", "Netflix",
    "Tesla", "NVIDIA", "AMD", "Intel", "Cisco", "Oracle",
    "IBM", "Qualcomm", "TexasInstruments", "Adobe", "Salesforce",
    "Palantir", "Coinbase", "MicroStrategy",
    # Banking/Finance
    "JPMorgan", "BankofAmerica", "WellsFargo", "Citigroup",
    "GoldmanSachs", "MorganStanley", "Visa", "Mastercard",
    "AmericanExpress", "BlackRock", "BerkshireHathaway",
    # Healthcare
    "JohnsonJohnson", "Pfizer", "Merck", "AbbVie", "Abbott",
    "ThermoFisher", "UnitedHealth", "Moderna", "BioNTech",
    # Consumer
    "McDonalds", "Starbucks", "CocaCola", "Pepsi", "Nike",
    "Walmart", "Costco", "Target", "HomeDepot", "Lowes",
    "Disney", "Netflix",
    # Industrial
    "Boeing", "FedEx", "UPS", "Caterpillar", "3M", "Honeywell",
    "GeneralElectric", "LockheedMartin", "Raytheon",
    # Energy
    "ExxonMobil", "Chevron", "ConocoPhillips", "Schlumberger",
    "BP", "Shell", "TotalEnergies",
    # European Stocks
    "SAP", "NovoNordisk", "Nestle", "Roche", "Novartis",
    "AstraZeneca", "HSBC", "Airbus", "Adidas", "LVMH",
    # Asian Stocks
    "Alibaba", "Tencent", "JDcom", "NetEase", "Baidu",
    "Samsung", "Toyota", "Sony", "Mitsubishi",
    # Other US Stocks
    "GameStop", "AMC", "MarathonDigital", "RiotBlockchain",
    "CoinbaseGlobal", "PalantirTechnologies", "Snowflake",
    "CrowdStrike", "Zoom", "Shopify", "Spotify",
]

STOCKS_OTC = [f"{stock}_otc" for stock in STOCKS]

# ============================================
# COMPLETE MASTER LIST
# ============================================

ALL_PAIRS = (
    FOREX_PAIRS + OTC_FOREX +
    INDICES + INDICES_OTC +
    COMMODITIES + COMMODITIES_OTC +
    CRYPTOS + CRYPTOS_OTC +
    STOCKS + STOCKS_OTC
)

# Category mapping
ALL_INSTRUMENTS = {
    "Forex": FOREX_PAIRS,
    "Forex-OTC": OTC_FOREX,
    "Indices": INDICES,
    "Indices-OTC": INDICES_OTC,
    "Commodities": COMMODITIES,
    "Commodities-OTC": COMMODITIES_OTC,
    "Crypto": CRYPTOS,
    "Crypto-OTC": CRYPTOS_OTC,
    "Stocks": STOCKS,
    "Stocks-OTC": STOCKS_OTC,
}

# ============================================
# FLAGS FOR DISPLAY
# ============================================

FLAGS = {
    # Forex Majors
    "EURUSD": "🇪🇺🇺🇸", "GBPUSD": "🇬🇧🇺🇸", "USDJPY": "🇺🇸🇯🇵",
    "AUDUSD": "🇦🇺🇺🇸", "USDCAD": "🇺🇸🇨🇦", "NZDUSD": "🇳🇿🇺🇸", "USDCHF": "🇺🇸🇨🇭",
    # Forex Minors
    "EURGBP": "🇪🇺🇬🇧", "EURJPY": "🇪🇺🇯🇵", "EURCHF": "🇪🇺🇨🇭", "EURCAD": "🇪🇺🇨🇦",
    "GBPJPY": "🇬🇧🇯🇵", "AUDJPY": "🇦🇺🇯🇵",
    # Exotics
    "USDZAR": "🇺🇸🇿🇦", "USDNGN": "🇺🇸🇳🇬", "USDKES": "🇺🇸🇰🇪", "USDTRY": "🇺🇸🇹🇷",
    "USDMXN": "🇺🇸🇲🇽", "USDBRL": "🇺🇸🇧🇷", "USDRUB": "🇺🇸🇷🇺", "USDSGD": "🇺🇸🇸🇬",
    # Indices
    "US100": "📊", "US30": "📈", "US500": "📊", "DJI30": "📈", "SP500": "📊",
    "GER30": "📊🇩🇪", "UK100": "📊🇬🇧", "FRA40": "📊🇫🇷", "JPN225": "📊🇯🇵",
    # Commodities
    "Gold": "🥇", "Silver": "🥈", "BrentOil": "🛢️", "WTICrudeOil": "🛢️", "NaturalGas": "🔥",
    # Crypto
    "Bitcoin": "₿", "Ethereum": "⟠", "Solana": "⚡", "Dogecoin": "🐕",
    # Stocks
    "Apple": "🍎", "Tesla": "🚗", "Microsoft": "💻", "Amazon": "📦", "Google": "🔍",
}

def get_flag(pair):
    """Get flag emoji for a pair"""
    base = pair.replace("_otc", "")
    return FLAGS.get(base, "🌍")

# ============================================
# TECHNICAL SETTINGS
# ============================================

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
SIGNAL_TIMER_MINUTES = 3
MARTINGALE_LEVELS = 3
MARTINGALE_INTERVAL = 3
SIGNAL_COOLDOWN_SECONDS = 300  # 5 minutes between same pair
MIN_CONFIDENCE = 50

# Priority pairs for initial subscription (top 20 most liquid)
PRIORITY_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "Gold", "Bitcoin",
    "US100", "Apple", "Tesla", "Silver", "Ethereum",
    "Microsoft", "Amazon", "US30", "EURGBP", "USDCHF",
]

print(f"✅ Loaded {len(ALL_PAIRS)} total instruments")
print(f"   Forex: {len(FOREX_PAIRS)} (+{len(OTC_FOREX)} OTC)")
print(f"   Indices: {len(INDICES)} (+{len(INDICES_OTC)} OTC)")
print(f"   Commodities: {len(COMMODITIES)} (+{len(COMMODITIES_OTC)} OTC)")
print(f"   Crypto: {len(CRYPTOS)} (+{len(CRYPTOS_OTC)} OTC)")
print(f"   Stocks: {len(STOCKS)} (+{len(STOCKS_OTC)} OTC)")
