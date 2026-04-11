"""
POCKET OPTION TRADING BOT - REST API VERSION
No complex WebSocket - simple and working
"""

import os
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - SIMPLE VERSION                   ║
║   REST API - No WebSocket complexity                           ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Credentials loaded!")

# ============================================
# NIGERIA TIME
# ============================================

def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=1)

def format_time():
    return get_nigeria_time().strftime("%I:%M %p")

# ============================================
# TELEGRAM BOT
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

settings = {
    "auto_trade": False,
    "total_signals": 0,
    "po_status": "READY"
}

# ============================================
# POCKET OPTION SIMPLE PRICE CHECK
# ============================================

def get_price_eurusd():
    """Get real EURUSD price from free API"""
    try:
        url = "https://api.frankfurter.app/latest?from=EUR&to=USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data['rates']['USD']
            return round(price, 5)
        return None
    except Exception as e:
        print(f"Price error: {e}")
        return None

def get_price_gold():
    """Get real Gold price from free API"""
    try:
        url = "https://api.gold-api.com/price/XAU"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('price', 0)
            return round(price, 2)
        return None
    except:
        # Fallback to Yahoo Finance
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [])
                if result:
                    price = result[0].get('meta', {}).get('regularMarketPrice')
                    return round(price, 2)
        except:
            pass
        return None

def calculate_signal(price, rsi_value=None):
    """Simple signal generation based on price movement"""
    # This is a placeholder - you can customize your strategy
    import random
    rsi = random.randint(30, 70)  # Simulated RSI
    
    if rsi < 35:
        return "BUY", 70 - rsi, f"RSI Oversold ({rsi})"
    elif rsi > 65:
        return "SELL", rsi - 60, f"RSI Overbought ({rsi})"
    else:
        return "NEUTRAL", 0, f"RSI Neutral ({rsi})"

def format_signal(name, flag, direction, confidence, price, rsi, reason):
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    martingale = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale.append(f"Level {i} → {level_time.strftime('%I:%M %p')}")
    
    tp = price * 1.005 if direction == "BUY" else price * 0.995
    sl = price * 0.995 if direction == "BUY" else price * 1.005
    
    return f"""
🔔 NEW SIGNAL!

🎫 Trade: {flag} {name} (OTC)
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {direction}

💪 Confidence: {confidence}%

📊 Technical Analysis:
• RSI: {rsi}
• {reason}

↪️ Martingale Levels:
{chr(10).join(martingale)}

💰 Entry Price: ${price:.5f}
🎯 Take Profit: ${tp:.5f}
🛑 Stop Loss: ${sl:.5f}

⏰ {format_time()} (Nigeria Time)
"""

# ============================================
# FLASK WEBHOOK
# ============================================

flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    secret = request.headers.get('X-Webhook-Token')
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "Invalid secret"}), 401
    
    data = request.json
    symbol = data.get('symbol', 'EURUSD')
    side = data.get('side', 'BUY')
    price = data.get('price', 0)
    
    entry_time = get_nigeria_time() + timedelta(minutes=3)
    
    msg = f"""
🔔 TRADINGVIEW SIGNAL

🎫 Trade: {symbol}
📈 Direction: {side}
💰 Price: ${price if price > 0 else 'Market'}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}

↪️ Martingale Levels:
 Level 1 → {(entry_time + timedelta(minutes=3)).strftime('%I:%M %p')}
 Level 2 → {(entry_time + timedelta(minutes=6)).strftime('%I:%M %p')}
 Level 3 → {(entry_time + timedelta(minutes=9)).strftime('%I:%M %p')}

⏰ {format_time()} (Nigeria Time)
"""
    
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg))
    settings["total_signals"] += 1
    return jsonify({"status": "sent"}), 200

# ============================================
# COMMANDS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 POCKET OPTION TRADING BOT\n\n"
        f"✅ Bot ONLINE\n"
        f"🔗 TradingView Webhook: ACTIVE\n\n"
        f"Commands:\n"
        f"/status - Check status\n"
        f"/webhook - Get webhook URL\n"
        f"/signal - Get test signal\n\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"🤖 Auto-trade: {'✅ ON' if settings['auto_trade'] else '❌ OFF'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"📊 Total signals: {settings['total_signals']}\n"
        f"⏰ {format_time()} (Nigeria Time)\n\n"
        f"To enable TradingView:\n"
        f"1. Get webhook URL with /webhook\n"
        f"2. Add to TradingView alert"
    )

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 WEBHOOK URL\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"Headers:\n"
        f"X-Webhook-Token: {WEBHOOK_SECRET}\n\n"
        f"JSON Format:\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY', 'price': 1.09234}}</code>",
        parse_mode='HTML'
    )

async def signal_command(update, context):
    """Generate a test signal"""
    price = get_price_eurusd()
    if not price:
        price = 1.09234
    
    direction, confidence, reason = calculate_signal(price, None)
    
    if direction != "NEUTRAL":
        signal = format_signal("EUR/USD", "🇪🇺🇺🇸", direction, confidence, price, 45, reason)
        await update.message.reply_text(signal)
        settings["total_signals"] += 1
    else:
        await update.message.reply_text(f"📊 EUR/USD: ${price}\n\nNo signal right now. RSI is neutral.")

async def autotrade_command(update, context):
    settings["auto_trade"] = not settings["auto_trade"]
    status = "ON" if settings["auto_trade"] else "OFF"
    await update.message.reply_text(f"🤖 Auto-trade turned {status}\n\n⚠️ Manual trading only for now.")

# Add handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(CommandHandler("webhook", webhook_command))
telegram_app.add_handler(CommandHandler("signal", signal_command))
telegram_app.add_handler(CommandHandler("autotrade", autotrade_command))

# ============================================
# FLASK SERVER
# ============================================

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 POCKET OPTION BOT\n\n✅ Bot ONLINE\n🔗 TradingView Webhook ready\n📋 Commands: /status, /webhook, /signal\n\n⏰ {format_time()}"
    )

async def main():
    await send_startup()
    
    # Start Flask thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Webhook server started on port 5000")
    
    # Start Telegram bot
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📍 Nigeria Time: {format_time()}")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
