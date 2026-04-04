"""
IQ TRADING BOT - STABLE VERSION (No HTML errors)
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
║   IQ TRADING BOT - STABLE EDITION                              ║
║   REAL-TIME SIGNALS | NIGERIA TIME                             ║
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

# Priority pairs that definitely work
PRIORITY_PAIRS = [
    {"name": "EUR/USD", "symbol": "EURUSD=X", "flag": "🇪🇺🇺🇸"},
    {"name": "GBP/USD", "symbol": "GBPUSD=X", "flag": "🇬🇧🇺🇸"},
    {"name": "USD/JPY", "symbol": "JPY=X", "flag": "🇺🇸🇯🇵"},
    {"name": "Gold", "symbol": "GC=F", "flag": "🥇"},
    {"name": "Bitcoin", "symbol": "BTC-USD", "flag": "₿"},
    {"name": "Ethereum", "symbol": "ETH-USD", "flag": "⟠"},
    {"name": "US100", "symbol": "^IXIC", "flag": "📊"},
    {"name": "Apple", "symbol": "AAPL", "flag": "🍎"},
    {"name": "Tesla", "symbol": "TSLA", "flag": "🚗"},
]

def get_price(symbol):
    """Get real price from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                price = result[0].get('meta', {}).get('regularMarketPrice')
                if price:
                    return round(price, 5 if price < 100 else 2)
        return None
    except Exception as e:
        print(f"Price error: {e}")
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
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
                closes = [c for c in closes if c is not None]
                if len(closes) > 14:
                    return calculate_rsi(closes)
        return 50
    except Exception as e:
        print(f"RSI error: {e}")
        return 50

def format_signal(pair_name, flag, direction, confidence, price, rsi, reason):
    """Format signal WITHOUT HTML parsing issues"""
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    martingale_lines = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale_lines.append(f"Level {i} -> {level_time.strftime('%I:%M %p')}")
    
    tp = price * 1.005 if direction == "BUY" else price * 0.995
    sl = price * 0.995 if direction == "BUY" else price * 1.005
    
    # Plain text message (no HTML formatting)
    message = f"""
🔔 NEW SIGNAL!

🎫 Trade: {flag} {pair_name}
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
    return message

async def monitor_pairs():
    print("🔄 Monitor started - checking every 30 seconds")
    
    while True:
        try:
            for pair in PRIORITY_PAIRS:
                try:
                    name = pair["name"]
                    symbol = pair["symbol"]
                    flag = pair["flag"]
                    
                    rsi = get_rsi(symbol)
                    price = get_price(symbol)
                    
                    if price is None:
                        continue
                    
                    current_time = datetime.now().timestamp()
                    last_time = settings["last_signal_time"].get(name, 0)
                    
                    if rsi <= 30 and (current_time - last_time) > 300:
                        settings["last_signal_time"][name] = current_time
                        settings["total_signals"] += 1
                        confidence = min(95, int(75 - rsi + 20))
                        reason = f"RSI Oversold ({rsi}) - Price may reverse UP"
                        message = format_signal(name, flag, "BUY", confidence, price, rsi, reason)
                        await bot.send_message(chat_id=CHAT_ID, text=message)
                        print(f"📤 SIGNAL SENT: {name} BUY (RSI: {rsi})")
                        
                    elif rsi >= 70 and (current_time - last_time) > 300:
                        settings["last_signal_time"][name] = current_time
                        settings["total_signals"] += 1
                        confidence = min(95, int(rsi - 70 + 20))
                        reason = f"RSI Overbought ({rsi}) - Price may reverse DOWN"
                        message = format_signal(name, flag, "SELL", confidence, price, rsi, reason)
                        await bot.send_message(chat_id=CHAT_ID, text=message)
                        print(f"📤 SIGNAL SENT: {name} SELL (RSI: {rsi})")
                    
                except Exception as e:
                    print(f"Error checking {pair.get('name')}: {e}")
                
                await asyncio.sleep(2)
            
            print(f"💓 Monitor cycle complete at {format_time()}")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Monitor error: {e}")
            await asyncio.sleep(30)

# Command handlers
async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 IQ TRADING BOT - STABLE EDITION\n\n"
        f"✅ Bot is ONLINE!\n\n"
        f"📈 Monitoring: EUR/USD, GBP/USD, USD/JPY, Gold, Bitcoin, Ethereum, US100, Apple, Tesla\n\n"
        f"⚡ Signal Mode: REAL-TIME\n"
        f"🎯 Trigger: RSI < 30 = BUY | RSI > 70 = SELL\n\n"
        f"⏰ Nigeria Time: {format_time()}\n\n"
        f"Signals will appear here automatically when RSI conditions are met!"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"🎯 Total signals sent: {settings['total_signals']}\n"
        f"⚡ Signal mode: REAL-TIME (RSI-based)\n"
        f"⏰ Time Zone: Nigeria (WAT)\n"
        f"🕐 Current Time: {format_time()}\n\n"
        f"Signal Trigger:\n"
        f"• RSI < 30 -> BUY signal\n"
        f"• RSI > 70 -> SELL signal"
    )

async def pairs_command(update, context):
    pairs_list = "\n".join([f"• {p['name']}" for p in PRIORITY_PAIRS])
    await update.message.reply_text(
        f"📊 MONITORED INSTRUMENTS\n\n{pairs_list}\n\n"
        f"Signals sent automatically when RSI < 30 (BUY) or RSI > 70 (SELL)"
    )

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("pairs", pairs_command))

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 IQ TRADING BOT - STABLE EDITION\n\n✅ Bot is ONLINE!\n\n📈 Monitoring 9 priority instruments\n⚡ REAL-TIME SIGNALS ACTIVE\n\nSignal Trigger:\n• RSI < 30 -> BUY\n• RSI > 70 -> SELL\n\n⏰ Nigeria Time: {format_time()}"
    )

async def main():
    await send_startup()
    print("🚀 Bot is running!")
    print(f"📍 Monitoring {len(PRIORITY_PAIRS)} instruments")
    print("📍 Commands: /status, /pairs")
    
    asyncio.create_task(monitor_pairs())
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
