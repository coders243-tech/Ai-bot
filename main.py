"""
IQ TRADING BOT - COMPLETE EDITION
RANDOM AUTO SIGNALS (7-10 MINUTES) | MANUAL ON/OFF CONTROL | NO DAILY LIMIT
"""

import os
import random
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   IQ TRADING BOT - COMPLETE EDITION                            ║
║   RANDOM SIGNALS (7-10 MINUTES) | MANUAL ON/OFF                ║
╚════════════════════════════════════════════════════════════════╝
""")

# Get credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

if not CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID not found!")
    exit(1)

print("✅ Credentials loaded!")

# Nigeria Time Zone (UTC+1)
def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=1)

def format_time(dt=None):
    if dt is None:
        dt = get_nigeria_time()
    return dt.strftime("%I:%M %p")

# Create bot
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Settings
settings = {
    "total_signals": 0,
    "last_signal_time": {},
    "min_interval_between_signals": 30,  # 30 seconds minimum between ANY signals
    "auto_signals_enabled": True  # Control auto signals on/off
}

# ============================================
# COMPLETE DICTIONARY - ALL PAIRS FROM YOUR IMAGES
# ============================================

ALL_PAIRS = {}

# ========== FOREX MAJORS & MINORS ==========
forex_pairs = [
    ("EUR/USD", "EURUSD=X", "🇪🇺🇺🇸"),
    ("GBP/USD", "GBPUSD=X", "🇬🇧🇺🇸"),
    ("USD/JPY", "JPY=X", "🇺🇸🇯🇵"),
    ("AUD/USD", "AUDUSD=X", "🇦🇺🇺🇸"),
    ("USD/CAD", "USDCAD=X", "🇺🇸🇨🇦"),
    ("NZD/USD", "NZDUSD=X", "🇳🇿🇺🇸"),
    ("USD/CHF", "CHF=X", "🇺🇸🇨🇭"),
    ("EUR/GBP", "EURGBP=X", "🇪🇺🇬🇧"),
    ("EUR/JPY", "EURJPY=X", "🇪🇺🇯🇵"),
    ("GBP/JPY", "GBPJPY=X", "🇬🇧🇯🇵"),
    ("AUD/JPY", "AUDJPY=X", "🇦🇺🇯🇵"),
    ("AUD/CAD", "AUDCAD=X", "🇦🇺🇨🇦"),
    ("CAD/JPY", "CADJPY=X", "🇨🇦🇯🇵"),
    ("CAD/CHF", "CADCHF=X", "🇨🇦🇨🇭"),
    ("CHF/JPY", "CHFJPY=X", "🇨🇭🇯🇵"),
    ("EUR/AUD", "EURAUD=X", "🇪🇺🇦🇺"),
    ("EUR/CAD", "EURCAD=X", "🇪🇺🇨🇦"),
    ("EUR/CHF", "EURCHF=X", "🇪🇺🇨🇭"),
    ("GBP/AUD", "GBPAUD=X", "🇬🇧🇦🇺"),
    ("GBP/CAD", "GBPCAD=X", "🇬🇧🇨🇦"),
    ("GBP/CHF", "GBPCHF=X", "🇬🇧🇨🇭"),
    ("AUD/CHF", "AUDCHF=X", "🇦🇺🇨🇭"),
    ("NZD/JPY", "NZDJPY=X", "🇳🇿🇯🇵"),
    ("EUR/NZD", "EURNZD=X", "🇪🇺🇳🇿"),
    ("GBP/NZD", "GBPNZD=X", "🇬🇧🇳🇿"),
]

for name, symbol, flag in forex_pairs:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Forex"}

# ========== EXOTIC FOREX (including ZAR, KES, etc.) ==========
exotic_pairs = [
    ("USD/ZAR", "USDZAR=X", "🇺🇸🇿🇦"),
    ("USD/TRY", "USDTRY=X", "🇺🇸🇹🇷"),
    ("USD/MXN", "USDMXN=X", "🇺🇸🇲🇽"),
    ("USD/SGD", "USDSGD=X", "🇺🇸🇸🇬"),
    ("USD/INR", "USDINR=X", "🇺🇸🇮🇳"),
    ("USD/BRL", "USDBRL=X", "🇺🇸🇧🇷"),
    ("USD/RUB", "USDRUB=X", "🇺🇸🇷🇺"),
    ("USD/THB", "USDTHB=X", "🇺🇸🇹🇭"),
    ("USD/IDR", "USDIDR=X", "🇺🇸🇮🇩"),
    ("USD/PHP", "USDPHP=X", "🇺🇸🇵🇭"),
    ("USD/PKR", "USDPKR=X", "🇺🇸🇵🇰"),
    ("USD/EGP", "USDEGP=X", "🇺🇸🇪🇬"),
    ("USD/MYR", "USDMYR=X", "🇺🇸🇲🇾"),
    ("USD/COP", "USDCOP=X", "🇺🇸🇨🇴"),
    ("USD/CLP", "USDCLP=X", "🇺🇸🇨🇱"),
    ("USD/ARS", "USDARS=X", "🇺🇸🇦🇷"),
    ("USD/BDT", "USDBDT=X", "🇺🇸🇧🇩"),
    ("USD/KES", "USDKES=X", "🇺🇸🇰🇪"),
    ("KES/USD", "KESUSD=X", "🇰🇪🇺🇸"),
    ("USD/NGN", "USDNGN=X", "🇺🇸🇳🇬"),
    ("NGN/USD", "NGNUSD=X", "🇳🇬🇺🇸"),
    ("USD/DZD", "USDDZD=X", "🇺🇸🇩🇿"),
    ("USD/TND", "USDTND=X", "🇺🇸🇹🇳"),
    ("USD/LBP", "USDLBP=X", "🇺🇸🇱🇧"),
    ("USD/UAH", "USDUAH=X", "🇺🇸🇺🇦"),
    ("EUR/TRY", "EURTRY=X", "🇪🇺🇹🇷"),
    ("EUR/RUB", "EURRUB=X", "🇪🇺🇷🇺"),
    ("EUR/HUF", "EURHUF=X", "🇪🇺🇭🇺"),
    ("EUR/ZAR", "EURZAR=X", "🇪🇺🇿🇦"),
]

for name, symbol, flag in exotic_pairs:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Forex"}

# ========== CNY CROSSES ==========
cny_pairs = [
    ("AED/CNY", "AEDCNY=X", "🇦🇪🇨🇳"),
    ("SAR/CNY", "SARCNY=X", "🇸🇦🇨🇳"),
    ("QAR/CNY", "QARCNY=X", "🇶🇦🇨🇳"),
    ("OMR/CNY", "OMRCNY=X", "🇴🇲🇨🇳"),
    ("BHD/CNY", "BHDCNY=X", "🇧🇭🇨🇳"),
    ("JOD/CNY", "JODCNY=X", "🇯🇴🇨🇳"),
    ("NGN/INR", "NGNINR=X", "🇳🇬🇮🇳"),
]

for name, symbol, flag in cny_pairs:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Forex"}

# ========== OTC FOREX ==========
otc_forex = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD", "USD/CHF",
              "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY", "USD/ZAR", "USD/TRY", "USD/MXN",
              "USD/INR", "USD/BRL", "USD/RUB", "USD/KES", "NGN/USD"]

for name in otc_forex:
    if name in ALL_PAIRS:
        ALL_PAIRS[f"{name}-OTC"] = {"symbol": ALL_PAIRS[name]["symbol"], "flag": ALL_PAIRS[name]["flag"], "type": "Forex-OTC"}

# ========== INDICES ==========
indices = [
    ("US100", "^IXIC", "📊"),
    ("US30", "^DJI", "📈"),
    ("US500", "^GSPC", "📊"),
    ("DJI30", "^DJI", "📈"),
    ("SP500", "^GSPC", "📊"),
    ("AEX 25", "^AEX", "📊🇳🇱"),
    ("CAC 40", "^FCHI", "📊🇫🇷"),
    ("D30/EUR", "^GDAXI", "📊🇩🇪"),
    ("E35EUR", "^IBEX", "📊🇪🇸"),
    ("E50/EUR", "^STOXX50E", "📊🇪🇺"),
    ("F40/EUR", "^FCHI", "📊🇫🇷"),
    ("HONG KONG 33", "^HSI", "📊🇭🇰"),
    ("JPN225", "^N225", "📊🇯🇵"),
    ("AUS 200", "^AXJO", "📊🇦🇺"),
    ("100GBP", "^FTSE", "📊🇬🇧"),
]

for name, symbol, flag in indices:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Index"}

# ========== INDICES OTC ==========
otc_indices = ["AUS 200", "100GBP", "D30/EUR", "DJI30", "E35EUR", "E50/EUR", "F40/EUR", "JPN225", "US100", "SP500"]
for name in otc_indices:
    if name in ALL_PAIRS:
        ALL_PAIRS[f"{name}-OTC"] = {"symbol": ALL_PAIRS[name]["symbol"], "flag": ALL_PAIRS[name]["flag"], "type": "Index-OTC"}

# ========== COMMODITIES ==========
commodities = [
    ("Gold", "GC=F", "🥇"),
    ("Silver", "SI=F", "🥈"),
    ("Brent Oil", "BZ=F", "🛢️"),
    ("WTI Crude Oil", "CL=F", "🛢️"),
    ("Natural Gas", "NG=F", "🔥"),
    ("Platinum", "PL=F", "🔘"),
    ("Palladium", "PA=F", "🔘"),
]

for name, symbol, flag in commodities:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Commodity"}
    ALL_PAIRS[f"{name}-OTC"] = {"symbol": symbol, "flag": flag, "type": "Commodity-OTC"}

# ========== CRYPTOCURRENCIES ==========
cryptos = [
    ("Bitcoin", "BTC-USD", "₿"),
    ("Ethereum", "ETH-USD", "⟠"),
    ("Solana", "SOL-USD", "⚡"),
    ("Cardano", "ADA-USD", "🟣"),
    ("Dogecoin", "DOGE-USD", "🐕"),
    ("Ripple", "XRP-USD", "✖️"),
    ("Litecoin", "LTC-USD", "Ł"),
]

for name, symbol, flag in cryptos:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Crypto"}
    ALL_PAIRS[f"{name}-OTC"] = {"symbol": symbol, "flag": flag, "type": "Crypto-OTC"}

# ========== STOCKS ==========
stocks = [
    ("Apple", "AAPL", "🍎"),
    ("Tesla", "TSLA", "🚗"),
    ("Microsoft", "MSFT", "💻"),
    ("Amazon", "AMZN", "📦"),
    ("Netflix", "NFLX", "🎬"),
    ("Google", "GOOGL", "🔍"),
    ("Meta", "META", "📘"),
    ("NVIDIA", "NVDA", "🎮"),
    ("AMD", "AMD", "💻"),
    ("Intel", "INTC", "💻"),
    ("Cisco", "CSCO", "🌐"),
    ("Johnson & Johnson", "JNJ", "💊"),
    ("McDonald's", "MCD", "🍔"),
    ("ExxonMobil", "XOM", "⛽"),
    ("FedEx", "FDX", "📦"),
    ("Boeing", "BA", "✈️"),
    ("Visa", "V", "💳"),
    ("JPMorgan", "JPM", "🏦"),
    ("Citigroup", "C", "🏦"),
    ("Pfizer", "PFE", "💊"),
    ("Alibaba", "BABA", "🛒"),
    ("Coinbase", "COIN", "₿"),
    ("GameStop", "GME", "🎮"),
    ("Marathon Digital", "MARA", "₿"),
    ("Palantir", "PLTR", "🔍"),
    ("American Express", "AXP", "💳"),
]

for name, symbol, flag in stocks:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Stock"}

# ========== STOCKS OTC ==========
otc_stocks = ["Apple", "Tesla", "Microsoft", "Amazon", "Netflix", "AMD", "Intel", "Cisco",
              "Johnson & Johnson", "McDonald's", "ExxonMobil", "FedEx", "Boeing", "Visa",
              "Citigroup", "Pfizer", "Alibaba", "Coinbase", "GameStop", "Marathon Digital",
              "Palantir", "American Express"]
for name in otc_stocks:
    if name in ALL_PAIRS:
        ALL_PAIRS[f"{name}-OTC"] = {"symbol": ALL_PAIRS[name]["symbol"], "flag": ALL_PAIRS[name]["flag"], "type": "Stock-OTC"}

# ========== EXTRA PAIRS ==========
extra_pairs = [
    ("MAD/USD", "MADUSD=X", "🇲🇦🇺🇸"),
    ("UAH/USD", "UAHUSD=X", "🇺🇦🇺🇸"),
    ("LBP/USD", "LBPUSD=X", "🇱🇧🇺🇸"),
    ("CHF/NOK", "CHFNOK=X", "🇨🇭🇳🇴"),
    ("MAD/USD-OTC", "MADUSD=X", "🇲🇦🇺🇸"),
    ("UAH/USD-OTC", "UAHUSD=X", "🇺🇦🇺🇸"),
    ("LBP/USD-OTC", "LBPUSD=X", "🇱🇧🇺🇸"),
]

for name, symbol, flag in extra_pairs:
    ALL_PAIRS[name] = {"symbol": symbol, "flag": flag, "type": "Forex"}

ALL_PAIR_NAMES = list(ALL_PAIRS.keys())
print(f"✅ Loaded {len(ALL_PAIRS)} tradable instruments")

# ============================================
# RATE LIMIT HELPERS
# ============================================

def get_random_interval():
    """Returns random interval between 7 and 10 minutes (in seconds)"""
    return random.randint(7 * 60, 10 * 60)  # 420 to 600 seconds

# ============================================
# PRICE & RSI FUNCTIONS
# ============================================

def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                price = result[0].get('meta', {}).get('regularMarketPrice')
                if price:
                    return round(price, 5 if price < 100 else 2)
        return None
    except:
        return None

def calculate_rsi(prices):
    if len(prices) < 15:
        return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    avg_gain = sum(gains[-14:]) / 14 if gains else 0
    avg_loss = sum(losses[-14:]) / 14 if losses else 0
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def get_rsi(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
                closes = [c for c in closes if c is not None]
                if len(closes) > 14:
                    return calculate_rsi(closes)
        return 50
    except:
        return 50

def format_signal(name, flag, direction, confidence, price, rsi, reason, is_manual=False):
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    martingale_lines = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale_lines.append(f"Level {i} -> {level_time.strftime('%I:%M %p')}")
    
    tp = price * 1.005 if direction == "BUY" else price * 0.995
    sl = price * 0.995 if direction == "BUY" else price * 1.005
    
    signal_type = "🔔 MANUAL SIGNAL" if is_manual else "🔔 NEW SIGNAL"
    
    return f"""
{signal_type}

🎫 Trade: {flag} {name}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {direction}

💪 Confidence: {confidence}%

📊 Technical Analysis:
• RSI: {rsi}
• {reason}

↪️ Martingale Levels:
{chr(10).join(martingale_lines)}

💰 Entry Price: ${price:.5f}
🎯 Take Profit: ${tp:.5f}
🛑 Stop Loss: ${sl:.5f}

⏰ {format_time()} (Nigeria Time)
"""

def get_signal_data(name, symbol, flag):
    price = get_price(symbol)
    if not price:
        return None
    
    rsi = get_rsi(symbol)
    
    if rsi <= 30:
        direction = "BUY"
        confidence = min(95, int(75 - rsi + 20))
        reason = f"RSI Oversold ({rsi}) - Price may reverse UP"
        return {"name": name, "flag": flag, "direction": direction, "confidence": confidence, "price": price, "rsi": rsi, "reason": reason}
    elif rsi >= 70:
        direction = "SELL"
        confidence = min(95, int(rsi - 70 + 20))
        reason = f"RSI Overbought ({rsi}) - Price may reverse DOWN"
        return {"name": name, "flag": flag, "direction": direction, "confidence": confidence, "price": price, "rsi": rsi, "reason": reason}
    return None

# ============================================
# AUTO MONITOR - RANDOM 7-10 MINUTE INTERVALS
# ============================================

async def monitor_pairs():
    print("🔄 Auto monitor started - random intervals between 7-10 minutes")
    print(f"📊 Total pairs to monitor: {len(ALL_PAIR_NAMES)}")
    print(f"🔘 Auto signals: {'ENABLED' if settings['auto_signals_enabled'] else 'DISABLED'}")
    
    while True:
        try:
            # Check if auto signals are enabled
            if not settings["auto_signals_enabled"]:
                print("💤 Auto signals disabled. Waiting...")
                await asyncio.sleep(60)
                continue
            
            # Shuffle pairs for random order
            shuffled_pairs = ALL_PAIR_NAMES.copy()
            random.shuffle(shuffled_pairs)
            
            signals_found = []
            
            for name in shuffled_pairs[:50]:  # Check 50 pairs per cycle
                if name not in ALL_PAIRS:
                    continue
                    
                pair = ALL_PAIRS[name]
                symbol = pair["symbol"]
                flag = pair["flag"]
                
                signal_data = get_signal_data(name, symbol, flag)
                
                if signal_data:
                    current_time = datetime.now().timestamp()
                    last_time = settings["last_signal_time"].get(name, 0)
                    last_any_signal = settings.get("last_any_signal", 0)
                    
                    # Check rate limits
                    if (current_time - last_time) < 1800:  # 30 min per same pair
                        continue
                    
                    if (current_time - last_any_signal) < settings["min_interval_between_signals"]:
                        continue
                    
                    # Send signal
                    settings["last_signal_time"][name] = current_time
                    settings["last_any_signal"] = current_time
                    settings["total_signals"] += 1
                    
                    message = format_signal(
                        signal_data["name"], signal_data["flag"],
                        signal_data["direction"], signal_data["confidence"],
                        signal_data["price"], signal_data["rsi"],
                        signal_data["reason"], is_manual=False
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"📤 SIGNAL: {name} {signal_data['direction']} (RSI: {signal_data['rsi']})")
                    signals_found.append(name)
                
                await asyncio.sleep(2)
            
            # Random interval between 7-10 minutes
            wait_seconds = get_random_interval()
            print(f"💓 Cycle complete. Found {len(signals_found)} signals. Next scan in {wait_seconds // 60} minutes {wait_seconds % 60} seconds")
            await asyncio.sleep(wait_seconds)
            
        except Exception as e:
            print(f"Monitor error: {e}")
            await asyncio.sleep(60)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 IQ TRADING BOT - COMPLETE EDITION\n\n"
        f"✅ Bot is ONLINE!\n\n"
        f"📈 Total instruments: {len(ALL_PAIRS)}\n"
        f"   • Forex: All majors, minors, exotics\n"
        f"   • Indices: US100, DJI30, SP500, etc.\n"
        f"   • Commodities: Gold, Silver, Oil\n"
        f"   • Crypto: Bitcoin, Ethereum, Solana\n"
        f"   • Stocks: Apple, Tesla, Microsoft\n\n"
        f"⚡ Auto-scan: Random intervals (7-10 minutes)\n"
        f"🎯 Trigger: RSI < 30 = BUY | RSI > 70 = SELL\n\n"
        f"📋 Commands:\n"
        f"   /signal [pair] - Manual signal\n"
        f"   /stop - Stop auto signals\n"
        f"   /startbot - Resume auto signals\n"
        f"   /pairs - List all pairs\n"
        f"   /status - Bot status\n\n"
        f"⏰ Nigeria Time: {format_time()}"
    )

async def stop_command(update, context):
    """Stop auto signals (manual signals still work)"""
    settings["auto_signals_enabled"] = False
    await update.message.reply_text(
        f"🛑 Auto signals STOPPED\n\n"
        f"Manual signals via /signal [pair] still work.\n"
        f"Type /startbot to resume auto signals.\n\n"
        f"⏰ Nigeria Time: {format_time()}"
    )
    print("🛑 Auto signals stopped by user command")

async def startbot_command(update, context):
    """Resume auto signals"""
    settings["auto_signals_enabled"] = True
    await update.message.reply_text(
        f"✅ Auto signals RESUMED!\n\n"
        f"Bot will now send signals automatically every 7-10 minutes.\n"
        f"Type /stop to turn off auto signals.\n\n"
        f"⏰ Nigeria Time: {format_time()}"
    )
    print("✅ Auto signals resumed by user command")

async def signal_command(update, context):
    if not context.args:
        sample = list(ALL_PAIRS.keys())[:30]
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair name]\n\n"
            f"Examples: /signal Gold\n"
            f"          /signal EUR/USD\n"
            f"          /signal Bitcoin\n"
            f"          /signal USD/ZAR\n\n"
            f"Available: {', '.join(sample)}...\n"
            f"Total: {len(ALL_PAIRS)} instruments\n\n"
            f"Type /pairs to see all categories"
        )
        return
    
    name = " ".join(context.args)
    
    # Try exact match
    if name not in ALL_PAIRS:
        found = None
        for key in ALL_PAIRS.keys():
            if key.lower() == name.lower():
                found = key
                break
        if found:
            name = found
        else:
            await update.message.reply_text(f"❌ '{name}' not found.\n\nType /pairs to see all instruments.")
            return
    
    pair = ALL_PAIRS[name]
    symbol = pair["symbol"]
    flag = pair["flag"]
    
    await update.message.reply_text(f"🔍 Analyzing {name}...")
    
    signal_data = get_signal_data(name, symbol, flag)
    
    if signal_data:
        message = format_signal(
            signal_data["name"], signal_data["flag"],
            signal_data["direction"], signal_data["confidence"],
            signal_data["price"], signal_data["rsi"],
            signal_data["reason"], is_manual=True
        )
        await update.message.reply_text(message)
        settings["total_signals"] += 1
    else:
        rsi = get_rsi(symbol)
        price = get_price(symbol) or 0
        await update.message.reply_text(
            f"📊 {name} Analysis\n\n"
            f"💰 Price: ${price:.5f}\n"
            f"📈 RSI: {rsi}\n\n"
            f"❌ No strong signal right now.\n"
            f"RSI is in neutral zone ({rsi}).\n\n"
            f"Signals are sent when RSI < 30 (BUY) or RSI > 70 (SELL)"
        )

async def pairs_command(update, context):
    forex = [p for p, info in ALL_PAIRS.items() if info["type"] in ["Forex", "Forex-OTC"]]
    indices = [p for p, info in ALL_PAIRS.items() if "Index" in info["type"]]
    commodities = [p for p, info in ALL_PAIRS.items() if "Commodity" in info["type"]]
    crypto = [p for p, info in ALL_PAIRS.items() if "Crypto" in info["type"]]
    stocks = [p for p, info in ALL_PAIRS.items() if "Stock" in info["type"]]
    
    await update.message.reply_text(
        f"📊 AVAILABLE INSTRUMENTS\n\n"
        f"Forex ({len(forex)}): {', '.join(forex[:20])}{'...' if len(forex) > 20 else ''}\n\n"
        f"Indices ({len(indices)}): {', '.join(indices[:15])}{'...' if len(indices) > 15 else ''}\n\n"
        f"Commodities ({len(commodities)}): {', '.join(commodities)}\n\n"
        f"Crypto ({len(crypto)}): {', '.join(crypto[:15])}{'...' if len(crypto) > 15 else ''}\n\n"
        f"Stocks ({len(stocks)}): {', '.join(stocks[:20])}{'...' if len(stocks) > 20 else ''}\n\n"
        f"TOTAL: {len(ALL_PAIRS)} instruments\n\n"
        f"Type /signal [name] for any instrument"
    )

async def status_command(update, context):
    auto_status = "🟢 ENABLED" if settings["auto_signals_enabled"] else "🔴 DISABLED"
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📈 Total instruments: {len(ALL_PAIRS)}\n"
        f"🎯 Total signals sent: {settings['total_signals']}\n"
        f"⚡ Auto signals: {auto_status}\n"
        f"⏰ Auto-scan interval: Random (7-10 minutes)\n"
        f"🎯 Trigger: RSI < 30 = BUY | RSI > 70 = SELL\n"
        f"⏰ Time Zone: Nigeria (WAT)\n"
        f"🕐 Current Time: {format_time()}\n\n"
        f"📋 Commands:\n"
        f"   /signal [pair] - Manual signal\n"
        f"   /stop - Stop auto signals\n"
        f"   /startbot - Resume auto signals\n"
        f"   /pairs - List all pairs\n"
        f"   /status - This menu"
    )

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("stop", stop_command))
application.add_handler(CommandHandler("startbot", startbot_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("status", status_command))

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 IQ TRADING BOT - COMPLETE EDITION\n\n✅ Bot is ONLINE!\n📈 Total instruments: {len(ALL_PAIRS)}\n⚡ Auto-scan: Random intervals (7-10 minutes)\n\n📋 Commands:\n/stop - Stop auto signals\n/startbot - Resume auto signals\n/signal [pair] - Manual signal\n\n⏰ Nigeria Time: {format_time()}"
    )

async def main():
    await send_startup()
    print(f"🚀 Bot is running!")
    print(f"📈 Total instruments: {len(ALL_PAIRS)}")
    print(f"⚡ Auto-scan: Random intervals between 7-10 minutes")
    print(f"🔘 Auto signals: {'ENABLED' if settings['auto_signals_enabled'] else 'DISABLED'}")
    print(f"📋 Commands: /signal, /stop, /startbot, /pairs, /status")
    
    asyncio.create_task(monitor_pairs())
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
