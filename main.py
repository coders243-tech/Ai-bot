"""
IQ TRADING BOT - COMPLETE EDITION
ALL PAIRS FROM YOUR IMAGES | RATE LIMITED SIGNALS
"""

import os
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
║   ALL PAIRS FROM YOUR IMAGES | RATE LIMITED SIGNALS            ║
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
    "last_signal_time": {}
}

# ============================================
# ALL PAIRS FROM YOUR IMAGES
# ============================================

ALL_PAIRS = {}

# ========== CURRENCIES from images ==========
currencies = [
    # From first image
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD", "USD/CHF",
    # From image 1000322200
    "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/CAD", "CAD/CHF", "CAD/JPY", "CHF/JPY", 
    "EUR/AUD", "EUR/CAD", "EUR/CHF", "GBP/AUD", "GBP/CAD", "GBP/CHF", "AUD/CHF",
    # From image 1000322206 (OTC)
    "EUR/GBP-OTC", "MAD/USD-OTC", "UAH/USD-OTC", "USD/BRL-OTC", "USD/DZD-OTC",
    "GBP/USD-OTC", "AUD/JPY-OTC", "USD/CLP-OTC", "GBP/AUD-OTC", "LBP/USD-OTC",
    # From image 1000322204
    "NGN/USD-OTC", "NZD/USD-OTC", "QAR/CNY-OTC", "SAR/CNY-OTC", "USD/CAD-OTC",
    "USD/COP-OTC", "USD/INR-OTC", "USD/MXN-OTC", "USD/PKR-OTC", "USD/RUB-OTC",
    # From image 1000322203
    "AUD/USD-OTC", "BHD/CNY-OTC", "CAD/CHF-OTC", "EUR/CHF-OTC", "EUR/JPY-OTC",
    "EUR/TRY-OTC", "EUR/USD-OTC", "GBP/JPY-OTC", "JOD/CNY-OTC", "KES/USD-OTC", "NGN/INR-OTC",
    # From image 1000322202
    "USD/SGD-OTC", "CHF/JPY-OTC", "USD/ARS-OTC", "USD/THB-OTC", "EUR/NZD-OTC",
    "USD/EGP-OTC", "USD/MYR-OTC", "OMR/CNY-OTC", "TND/USD-OTC", "USD/IDR-OTC", "FIIR/GRP-OTC",
    # From image 1000322191
    "YER/USD-OTC", "AED/CNY-OTC", "USD/CHF-OTC", "CHF/NOK-OTC", "NZD/JPY-OTC",
    "USD/BDT-OTC", "USD/JPY-OTC", "CAD/JPY-OTC", "EUR/HUF-OTC", "EUR/RUB-OTC", "USD/PHP-OTC",
]

for pair in currencies:
    base_pair = pair.replace("-OTC", "")
    if "OTC" in pair:
        ALL_PAIRS[pair] = {"symbol": f"{base_pair.replace('/', '')}=X", "flag": "🌍", "type": "Forex-OTC"}
    else:
        ALL_PAIRS[pair] = {"symbol": f"{pair.replace('/', '')}=X", "flag": "🌍", "type": "Forex"}

# ========== INDICES from images ==========
indices = [
    "AEX 25", "CAC 40", "D30/EUR", "DJI30", "E35EUR", "E50/EUR", "F40/EUR",
    "HONG KONG 33", "JPN225", "US100", "AUS 200", "100GBP", "SP500",
    # OTC versions
    "AUS 200-OTC", "100GBP-OTC", "D30EUR-OTC", "DJI30-OTC", "E35EUR-OTC",
    "E50EUR-OTC", "F40EUR-OTC", "JPN225-OTC", "US100-OTC", "SP500-OTC"
]

for idx in indices:
    if "OTC" in idx:
        name = idx.replace("-OTC", "")
        ALL_PAIRS[idx] = {"symbol": "^" + name.replace(" ", "").replace("/", ""), "flag": "📊", "type": "Index-OTC"}
    else:
        ALL_PAIRS[idx] = {"symbol": "^" + idx.replace(" ", "").replace("/", ""), "flag": "📊", "type": "Index"}

# ========== COMMODITIES from images ==========
commodities = [
    "Gold", "Silver", "Brent Oil", "WTI Crude Oil", "Natural Gas", "Platinum spot", "Palladium spot",
    "Gold-OTC", "Silver-OTC", "Brent Oil-OTC", "WTI Crude Oil-OTC", "Natural Gas-OTC",
    "Platinum spot-OTC", "Palladium spot-OTC"
]

for comm in commodities:
    if "Gold" in comm:
        ALL_PAIRS[comm] = {"symbol": "GC=F", "flag": "🥇", "type": "Commodity"}
    elif "Silver" in comm:
        ALL_PAIRS[comm] = {"symbol": "SI=F", "flag": "🥈", "type": "Commodity"}
    elif "Brent" in comm:
        ALL_PAIRS[comm] = {"symbol": "BZ=F", "flag": "🛢️", "type": "Commodity"}
    elif "WTI" in comm:
        ALL_PAIRS[comm] = {"symbol": "CL=F", "flag": "🛢️", "type": "Commodity"}
    elif "Natural Gas" in comm:
        ALL_PAIRS[comm] = {"symbol": "NG=F", "flag": "🔥", "type": "Commodity"}
    elif "Platinum" in comm:
        ALL_PAIRS[comm] = {"symbol": "PL=F", "flag": "🔘", "type": "Commodity"}
    elif "Palladium" in comm:
        ALL_PAIRS[comm] = {"symbol": "PA=F", "flag": "🔘", "type": "Commodity"}

# ========== CRYPTOCURRENCIES from images ==========
cryptos = [
    "Bitcoin", "Ethereum", "Solana", "Cardano", "Dogecoin", "Ripple", "Litecoin",
    "Chainlink", "Avalanche", "Polygon", "TRON",
    "Bitcoin-OTC", "Ethereum-OTC", "Solana-OTC", "Cardano-OTC", "Dogecoin-OTC",
    "Chainlink-OTC", "Litecoin-OTC", "Avalanche-OTC", "TRON-OTC", "Polygon-OTC"
]

for crypto in cryptos:
    base = crypto.replace("-OTC", "").lower()
    if "bitcoin" in base:
        ALL_PAIRS[crypto] = {"symbol": "BTC-USD", "flag": "₿", "type": "Crypto"}
    elif "ethereum" in base:
        ALL_PAIRS[crypto] = {"symbol": "ETH-USD", "flag": "⟠", "type": "Crypto"}
    elif "solana" in base:
        ALL_PAIRS[crypto] = {"symbol": "SOL-USD", "flag": "⚡", "type": "Crypto"}
    elif "cardano" in base:
        ALL_PAIRS[crypto] = {"symbol": "ADA-USD", "flag": "🟣", "type": "Crypto"}
    elif "dogecoin" in base:
        ALL_PAIRS[crypto] = {"symbol": "DOGE-USD", "flag": "🐕", "type": "Crypto"}
    elif "ripple" in base:
        ALL_PAIRS[crypto] = {"symbol": "XRP-USD", "flag": "✖️", "type": "Crypto"}
    elif "litecoin" in base:
        ALL_PAIRS[crypto] = {"symbol": "LTC-USD", "flag": "Ł", "type": "Crypto"}
    elif "chainlink" in base:
        ALL_PAIRS[crypto] = {"symbol": "LINK-USD", "flag": "🔗", "type": "Crypto"}
    elif "avalanche" in base:
        ALL_PAIRS[crypto] = {"symbol": "AVAX-USD", "flag": "🔺", "type": "Crypto"}
    elif "polygon" in base:
        ALL_PAIRS[crypto] = {"symbol": "MATIC-USD", "flag": "🟣", "type": "Crypto"}
    elif "tron" in base:
        ALL_PAIRS[crypto] = {"symbol": "TRX-USD", "flag": "🔴", "type": "Crypto"}

# ========== STOCKS from images ==========
stocks = [
    "Apple", "Tesla", "Microsoft", "Amazon", "Netflix", "Google", "Meta", "NVIDIA",
    "AMD", "Intel", "Cisco", "Johnson & Johnson", "McDonald's", "ExxonMobil",
    "FedEx", "Boeing", "Visa", "JPMorgan", "Citigroup", "Pfizer", "Alibaba",
    "Coinbase", "GameStop", "Marathon Digital", "Palantir", "American Express",
    "VIX", "Facebook Inc", "Citi", "JPMorgan Chase & Co",
    # OTC versions
    "Apple-OTC", "Tesla-OTC", "Microsoft-OTC", "Amazon-OTC", "Netflix-OTC",
    "AMD-OTC", "Intel-OTC", "Cisco-OTC", "Johnson & Johnson-OTC", "McDonald's-OTC",
    "ExxonMobil-OTC", "FedEx-OTC", "Boeing Company-OTC", "VISA-OTC", "Citigroup Inc-OTC",
    "Pfizer Inc-OTC", "Alibaba-OTC", "Coinbase Global-OTC", "GameStop Corp-OTC",
    "Marathon Digital Holdings-OTC", "Palantir Technologies-OTC", "American Express-OTC",
    "VIX-OTC", "Facebook Inc-OTC", "Citi-OTC"
]

stock_symbols = {
    "Apple": "AAPL", "Tesla": "TSLA", "Microsoft": "MSFT", "Amazon": "AMZN",
    "Netflix": "NFLX", "Google": "GOOGL", "Meta": "META", "NVIDIA": "NVDA",
    "AMD": "AMD", "Intel": "INTC", "Cisco": "CSCO", "Johnson & Johnson": "JNJ",
    "McDonald's": "MCD", "ExxonMobil": "XOM", "FedEx": "FDX", "Boeing": "BA",
    "Visa": "V", "JPMorgan": "JPM", "Citigroup": "C", "Pfizer": "PFE",
    "Alibaba": "BABA", "Coinbase": "COIN", "GameStop": "GME", "Marathon Digital": "MARA",
    "Palantir": "PLTR", "American Express": "AXP", "VIX": "^VIX", "Facebook Inc": "META",
    "Citi": "C", "JPMorgan Chase & Co": "JPM"
}

for stock in stocks:
    base = stock.replace("-OTC", "")
    if base in stock_symbols:
        ALL_PAIRS[stock] = {"symbol": stock_symbols[base], "flag": "📈", "type": "Stock"}

print(f"✅ Loaded {len(ALL_PAIRS)} tradable instruments")

# Priority pairs for auto-scan (spread out - no duplicates)
AUTO_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "Gold", "Bitcoin", "US100", "Apple", "Tesla",
    "Silver", "Ethereum", "DJI30", "Microsoft", "EUR/GBP", "Solana", "Amazon"
]

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
    
    signal_type = "MANUAL SIGNAL" if is_manual else "NEW SIGNAL"
    
    return f"""
🔔 {signal_type}!

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
# AUTO MONITOR WITH RATE LIMITING
# ============================================

async def monitor_pairs():
    print("🔄 Auto monitor started - checking every 60 seconds")
    print(f"📊 Monitoring {len(AUTO_PAIRS)} priority pairs")
    
    while True:
        try:
            for i, name in enumerate(AUTO_PAIRS):
                if name not in ALL_PAIRS:
                    continue
                    
                pair = ALL_PAIRS[name]
                symbol = pair["symbol"]
                flag = pair["flag"]
                
                signal_data = get_signal_data(name, symbol, flag)
                
                if signal_data:
                    current_time = datetime.now().timestamp()
                    last_time = settings["last_signal_time"].get(name, 0)
                    
                    # Rate limit: 30 minutes between signals for same pair
                    if (current_time - last_time) > 1800:
                        settings["last_signal_time"][name] = current_time
                        settings["total_signals"] += 1
                        
                        message = format_signal(
                            signal_data["name"], signal_data["flag"],
                            signal_data["direction"], signal_data["confidence"],
                            signal_data["price"], signal_data["rsi"],
                            signal_data["reason"], is_manual=False
                        )
                        await bot.send_message(chat_id=CHAT_ID, text=message)
                        print(f"📤 AUTO SIGNAL: {name} {signal_data['direction']} (RSI: {signal_data['rsi']})")
                    else:
                        minutes_left = int(1800 - (current_time - last_time)) // 60
                        print(f"⏳ Rate limited: {name} - next signal in {minutes_left} min")
                
                # Stagger the API calls
                await asyncio.sleep(5)
            
            print(f"💓 Monitor cycle complete at {format_time()}")
            await asyncio.sleep(60)  # Wait 1 minute before next full cycle
            
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
        f"   • Forex: 80+ pairs (including OTC)\n"
        f"   • Indices: 20+ (including OTC)\n"
        f"   • Commodities: 14 (including OTC)\n"
        f"   • Crypto: 20+ (including OTC)\n"
        f"   • Stocks: 50+ (including OTC)\n\n"
        f"⚡ Signal Mode: REAL-TIME (rate limited to 30 min per pair)\n"
        f"🎯 Trigger: RSI < 30 = BUY | RSI > 70 = SELL\n\n"
        f"📋 Commands:\n"
        f"   /signal [pair] - Manual signal\n"
        f"   /pairs - List all pairs\n"
        f"   /status - Bot status\n\n"
        f"⏰ Nigeria Time: {format_time()}"
    )

async def signal_command(update, context):
    if not context.args:
        sample = list(ALL_PAIRS.keys())[:20]
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair name]\n\n"
            f"Examples: /signal Gold\n"
            f"          /signal EUR/USD\n"
            f"          /signal Bitcoin\n\n"
            f"Available: {', '.join(sample)}...\n"
            f"Total: {len(ALL_PAIRS)} instruments"
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
    forex = [p for p, info in ALL_PAIRS.items() if "Forex" in info["type"]]
    indices = [p for p, info in ALL_PAIRS.items() if "Index" in info["type"]]
    commodities = [p for p, info in ALL_PAIRS.items() if info["type"] == "Commodity"]
    crypto = [p for p, info in ALL_PAIRS.items() if info["type"] == "Crypto"]
    stocks = [p for p, info in ALL_PAIRS.items() if info["type"] == "Stock"]
    
    await update.message.reply_text(
        f"📊 AVAILABLE INSTRUMENTS\n\n"
        f"Forex ({len(forex)}): {', '.join(forex[:15])}{'...' if len(forex) > 15 else ''}\n\n"
        f"Indices ({len(indices)}): {', '.join(indices[:10])}{'...' if len(indices) > 10 else ''}\n\n"
        f"Commodities ({len(commodities)}): {', '.join(commodities)}\n\n"
        f"Crypto ({len(crypto)}): {', '.join(crypto[:10])}{'...' if len(crypto) > 10 else ''}\n\n"
        f"Stocks ({len(stocks)}): {', '.join(stocks[:15])}{'...' if len(stocks) > 15 else ''}\n\n"
        f"Total: {len(ALL_PAIRS)} instruments\n\n"
        f"Type /signal [name] for any instrument"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📈 Total instruments: {len(ALL_PAIRS)}\n"
        f"🎯 Total signals sent: {settings['total_signals']}\n"
        f"⚡ Auto-scan: {len(AUTO_PAIRS)} priority pairs\n"
        f"⏰ Rate limit: 30 minutes between signals per pair\n"
        f"🎯 Signal trigger: RSI < 30 = BUY | RSI > 70 = SELL\n"
        f"⏰ Time Zone: Nigeria (WAT)\n"
        f"🕐 Current Time: {format_time()}\n\n"
        f"📋 Commands:\n"
        f"   /signal [pair] - Manual signal\n"
        f"   /pairs - List all pairs\n"
        f"   /status - This menu"
    )

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("status", status_command))

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 IQ TRADING BOT - COMPLETE EDITION\n\n✅ Bot is ONLINE!\n📈 Total instruments: {len(ALL_PAIRS)}\n⚡ Auto-signals rate limited to 30 min per pair\n🎯 Type /signal [pair] for manual analysis\n\n⏰ Nigeria Time: {format_time()}"
    )

async def main():
    await send_startup()
    print(f"🚀 Bot is running!")
    print(f"📈 Total instruments: {len(ALL_PAIRS)}")
    print(f"🔄 Auto-monitoring {len(AUTO_PAIRS)} priority pairs")
    print(f"⏰ Rate limit: 30 minutes between signals per pair")
    print(f"📋 Commands: /signal [pair], /pairs, /status")
    
    asyncio.create_task(monitor_pairs())
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
