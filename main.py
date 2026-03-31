"""
IQ TRADING BOT - PROFESSIONAL EDITION
Working with Nigeria Time Zone (WAT)
"""

import os
import time
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔══════════════════════════════════════╗
║   IQ TRADING BOT - PROFESSIONAL      ║
║   Nigeria Time Zone (WAT)            ║
╚══════════════════════════════════════╝
""")

# Get credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Bot initialized!")

# Nigeria Time Zone (UTC+1)
def get_nigeria_time():
    """Returns current time in Nigeria (WAT)"""
    utc_now = datetime.utcnow()
    nigeria_time = utc_now + timedelta(hours=1)
    return nigeria_time

def format_time():
    """Format time for display"""
    return get_nigeria_time().strftime("%I:%M %p")

def format_full_time():
    """Format full date and time"""
    return get_nigeria_time().strftime("%Y-%m-%d %I:%M:%S %p")

# Create bot
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Settings
settings = {
    "min_confidence": 20,
    "total_scans": 0,
    "total_signals": 0
}

# Currency pairs to monitor
PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X", 
    "USDJPY": "JPY=X",
    "XAUUSD": "GC=F"
}

# ============ FUNCTION TO GET REAL PRICE ============

def get_forex_price(pair_symbol):
    """Get real price from Yahoo Finance (FREE, no API key needed!)"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair_symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                price = result[0].get('meta', {}).get('regularMarketPrice')
                if price:
                    return round(price, 5)
        return None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def calculate_rsi(prices):
    """Simple RSI calculation"""
    if len(prices) < 15:
        return 50
    
    gains = []
    losses = []
    
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
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

def generate_signal(pair_name, pair_symbol):
    """Generate real trading signal with Nigeria time"""
    # Get current price
    price = get_forex_price(pair_symbol)
    
    if not price:
        return None
    
    # Get historical data for RSI (simplified)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair_symbol}?range=1d&interval=5m"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
                closes = [c for c in closes if c is not None]
                
                if len(closes) > 14:
                    rsi = calculate_rsi(closes)
                else:
                    rsi = 50
            else:
                rsi = 50
        else:
            rsi = 50
    except:
        rsi = 50
    
    # Generate signal based on RSI
    if rsi < 30:
        direction = "BUY"
        confidence = 75 - rsi
        signal_type = "STRONG_BUY"
        emoji = "🟢🟢"
        reason = f"RSI Oversold ({rsi}) - Price may reverse UP"
    elif rsi > 70:
        direction = "SELL"
        confidence = rsi - 70
        signal_type = "STRONG_SELL"
        emoji = "🔴🔴"
        reason = f"RSI Overbought ({rsi}) - Price may reverse DOWN"
    elif rsi < 40:
        direction = "BUY"
        confidence = 40
        signal_type = "BUY"
        emoji = "🟢"
        reason = f"RSI Approaching Oversold ({rsi})"
    elif rsi > 60:
        direction = "SELL"
        confidence = 40
        signal_type = "SELL"
        emoji = "🔴"
        reason = f"RSI Approaching Overbought ({rsi})"
    else:
        direction = "NEUTRAL"
        confidence = 20
        signal_type = "NEUTRAL"
        emoji = "⚪"
        reason = f"RSI Neutral ({rsi}) - No clear signal"
    
    return {
        'pair': pair_name,
        'symbol': pair_symbol,
        'price': price,
        'rsi': rsi,
        'direction': direction,
        'confidence': confidence,
        'signal_type': signal_type,
        'emoji': emoji,
        'reason': reason,
        'timestamp': format_time(),
        'full_time': format_full_time()
    }

# ============ COMMAND HANDLERS ============

async def start_command(update, context):
    await update.message.reply_text(f"""
🤖 <b>IQ TRADING BOT - PROFESSIONAL EDITION</b>

✅ Bot is ONLINE with REAL market data!

📈 <b>Features:</b>
• Real-time forex prices
• RSI technical analysis
• Buy/Sell signals
• 24/7 monitoring
• Nigeria Time Zone (WAT)

⏰ <b>Current Time:</b> {format_time()}

📋 Type /help for commands
""", parse_mode='HTML')

async def help_command(update, context):
    await update.message.reply_text(f"""
📋 <b>COMMANDS</b>

/status - Bot status and statistics
/signal [pair] - Get signal (EURUSD, GBPUSD, USDJPY, XAUUSD)
/scan - Scan all pairs for signals
/confidence [value] - Set confidence threshold (10-90)
/stats - Trading statistics

<b>Examples:</b>
/signal EURUSD
/signal XAUUSD
/confidence 25

⏰ Nigeria Time: {format_time()}
""", parse_mode='HTML')

async def status_command(update, context):
    status_text = f"""
📊 <b>BOT STATUS</b>

✅ Status: ONLINE
📈 Active pairs: 4
🎯 Min confidence: {settings['min_confidence']}%
📊 Total scans: {settings['total_scans']}
🎯 Total signals: {settings['total_signals']}
📱 Platform: Railway Cloud
⏰ Time Zone: Nigeria (WAT)
🕐 Current Time: {format_time()}

<b>Data Source:</b> Yahoo Finance (FREE)
<b>Analysis:</b> RSI (Relative Strength Index)
"""
    await update.message.reply_text(status_text, parse_mode='HTML')

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text(f"""
⚠️ Usage: /signal EURUSD

Available pairs: EURUSD, GBPUSD, USDJPY, XAUUSD

Example: /signal EURUSD

⏰ Nigeria Time: {format_time()}
""")
        return
    
    pair = context.args[0].upper()
    
    if pair not in PAIRS:
        await update.message.reply_text(f"❌ Pair '{pair}' not supported.\n\nAvailable: EURUSD, GBPUSD, USDJPY, XAUUSD")
        return
    
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    # Get real signal
    signal = generate_signal(pair, PAIRS[pair])
    
    if signal:
        message = f"""
{signal['emoji']} <b>{signal['direction']} {signal['pair']}</b> {signal['emoji']}

💰 <b>Current Price:</b> ${signal['price']}
📈 <b>RSI (14):</b> {signal['rsi']}
🎯 <b>Confidence:</b> {signal['confidence']}%
📊 <b>Analysis:</b> {signal['reason']}

⏰ <b>Signal Time:</b> {signal['timestamp']} (Nigeria Time)
        """
        await update.message.reply_text(message, parse_mode='HTML')
        settings['total_signals'] += 1
    else:
        await update.message.reply_text(f"❌ Could not fetch data for {pair}. Please try again.")

async def scan_command(update, context):
    await update.message.reply_text(f"🔍 Scanning all pairs for signals...\n⏰ {format_time()}")
    
    settings['total_scans'] += 1
    signals_found = []
    
    for pair_name, pair_symbol in PAIRS.items():
        signal = generate_signal(pair_name, pair_symbol)
        if signal and signal['confidence'] >= settings['min_confidence'] and signal['direction'] != "NEUTRAL":
            signals_found.append(f"• {signal['direction']} {pair_name} | RSI: {signal['rsi']} | Conf: {signal['confidence']}%")
        await asyncio.sleep(1)
    
    if signals_found:
        result = "\n".join(signals_found)
        await update.message.reply_text(f"""
🔍 <b>SCAN COMPLETE!</b>

✅ Found {len(signals_found)} signal(s):

{result}

Use /signal [PAIR] for detailed analysis

⏰ {format_time()} (Nigeria Time)
""", parse_mode='HTML')
        settings['total_signals'] += len(signals_found)
    else:
        await update.message.reply_text(f"""
🔍 <b>SCAN COMPLETE!</b>

❌ No strong signals found.

📊 Confidence threshold: {settings['min_confidence']}%

💡 Try /confidence 15 for more signals

⏰ {format_time()} (Nigeria Time)
""", parse_mode='HTML')

async def confidence_command(update, context):
    if not context.args:
        await update.message.reply_text(f"⚠️ Current min confidence: {settings['min_confidence']}\n\nUsage: /confidence 25\n\n⏰ {format_time()}")
        return
    
    try:
        new_conf = int(context.args[0])
        if 10 <= new_conf <= 90:
            settings['min_confidence'] = new_conf
            await update.message.reply_text(f"✅ Min confidence set to {new_conf}\n\nOnly signals with {new_conf}+ confidence will be shown.\n\n⏰ {format_time()}")
        else:
            await update.message.reply_text("❌ Please enter a value between 10 and 90")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")

async def stats_command(update, context):
    await update.message.reply_text(f"""
📊 <b>TRADING STATISTICS</b>

Total scans: {settings['total_scans']}
Total signals: {settings['total_signals']}
Min confidence: {settings['min_confidence']}
Active pairs: 4

<b>Data Source:</b> Yahoo Finance
<b>Analysis Method:</b> RSI (14-period)
<b>Uptime:</b> 24/7 on Railway
<b>Time Zone:</b> Nigeria (WAT)

⏰ {format_time()}
""", parse_mode='HTML')

# ============ AUTO SCAN ============

async def auto_scan():
    """Automatic scan every 15 minutes"""
    print(f"🔍 Auto-scan at {format_full_time()}")
    settings['total_scans'] += 1
    
    for pair_name, pair_symbol in PAIRS.items():
        signal = generate_signal(pair_name, pair_symbol)
        if signal and signal['confidence'] >= settings['min_confidence'] and signal['direction'] != "NEUTRAL":
            message = f"""
{signal['emoji']} <b>{signal['direction']} {signal['pair']}</b> {signal['emoji']}

💰 <b>Price:</b> ${signal['price']}
📈 <b>RSI:</b> {signal['rsi']}
🎯 <b>Confidence:</b> {signal['confidence']}%
📊 {signal['reason']}

⏰ {signal['timestamp']} (Nigeria Time)
            """
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
            settings['total_signals'] += 1
        await asyncio.sleep(2)

def run_auto_scan():
    asyncio.run(auto_scan())

# ============ STARTUP MESSAGE ============

async def send_startup():
    await bot.send_message(chat_id=CHAT_ID, text=f"""
🤖 <b>IQ TRADING BOT - PROFESSIONAL EDITION</b>

✅ Bot is ONLINE with REAL market data!

📈 <b>Monitoring:</b>
• EURUSD (Euro/US Dollar)
• GBPUSD (British Pound/US Dollar)
• USDJPY (US Dollar/Japanese Yen)
• XAUUSD (Gold)

⚙️ <b>Analysis:</b> RSI (14-period)
🎯 <b>Confidence threshold:</b> 20%
⏰ <b>Time Zone:</b> Nigeria (WAT)
🕐 <b>Current Time:</b> {format_time()}

📋 Try these commands:
/signal EURUSD - Get real signal
/scan - Scan all pairs
/status - Check bot health

<i>Signals update in real-time with Nigeria time!</i>
""", parse_mode='HTML')

# ============ ADD COMMAND HANDLERS ============

application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("scan", scan_command))
application.add_handler(CommandHandler("confidence", confidence_command))
application.add_handler(CommandHandler("stats", stats_command))

# ============ START AUTO-SCAN THREAD ============

import threading
def run_schedule():
    while True:
        time.sleep(900)  # 15 minutes
        run_auto_scan()

schedule_thread = threading.Thread(target=run_schedule, daemon=True)
schedule_thread.start()

# ============ RUN BOT ============

# Send startup message
asyncio.run(send_startup())

print("""
🚀 BOT IS RUNNING!
📊 Using Yahoo Finance (NO API key needed!)
📍 Nigeria Time Zone (WAT)
📍 Commands: /signal EURUSD, /scan, /status
📍 Auto-scan every 15 minutes
📍 Press Ctrl+C to stop
""")

application.run_polling(allowed_updates=True)
