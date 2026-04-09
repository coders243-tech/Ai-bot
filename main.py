"""
POCKET OPTION TRADING BOT - WORKING VERSION
Direct connection to Pocket Option WebSocket
"""

import os
import json
import asyncio
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler
import websocket

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - WORKING VERSION                  ║
║   Direct WebSocket Connection                                  ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")

# Your Pocket Option credentials
SSID = "0d3ef4dafc05966efc12800ba7963e78"
UID = "29984823"

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

print("✅ Credentials loaded!")
print(f"📡 SSID: {SSID}")
print(f"👤 UID: {UID}")

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
    "ws_connected": False,
    "auto_trade": False,
    "total_signals": 0
}

# ============================================
# POCKET OPTION WEBSOCKET
# ============================================

PO_WS_URL = "wss://api.pocketoption.com/socket.io/?EIO=4&transport=websocket"

def on_message(ws, message):
    """Handle incoming messages from Pocket Option"""
    try:
        print(f"📨 Message: {message[:150]}")
        
        # Check for successful auth
        if '"status":true' in message or '"success":true' in message:
            print("✅ Pocket Option authentication successful!")
            settings["ws_connected"] = True
            
            # Send a test message to Telegram
            asyncio.run(bot.send_message(
                chat_id=CHAT_ID,
                text=f"✅ Pocket Option CONNECTED!\n💰 Demo account ready\n⏰ {format_time()}"
            ))
        
        # Check for price data
        if '"price"' in message or '"candle"' in message:
            print("💰 Price data received")
            
    except Exception as e:
        print(f"Error in on_message: {e}")

def on_error(ws, error):
    print(f"❌ WebSocket error: {error}")
    settings["ws_connected"] = False

def on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed")
    settings["ws_connected"] = False

def on_open(ws):
    print("✅ WebSocket connected to Pocket Option!")
    
    # Step 1: Send authentication message
    auth_msg = f'42["auth",{{"session":"{SSID}","isDemo":1,"uid":{UID},"platform":1}}]'
    ws.send(auth_msg)
    print("🔐 Auth message sent")
    
    # Step 2: Subscribe to price updates for EURUSD
    subscribe_msg = '42["subscribe",{"name":"candle-1-EURUSD"}]'
    ws.send(subscribe_msg)
    print("📊 Subscribed to EURUSD")

def start_websocket():
    """Start WebSocket connection in background thread"""
    try:
        ws = websocket.WebSocketApp(
            PO_WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket in a separate thread
        wst = threading.Thread(target=ws.run_forever, daemon=True)
        wst.start()
        print("🚀 WebSocket thread started")
        return ws
    except Exception as e:
        print(f"❌ Failed to start WebSocket: {e}")
        return None

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
    
    # Send to Telegram
    msg = f"""
🔔 TRADINGVIEW SIGNAL

🎫 Trade: {symbol}
📈 Direction: {side}
⏳ Timer: 3 minutes
➡️ Entry: {(get_nigeria_time() + timedelta(minutes=3)).strftime('%I:%M %p')}

↪️ Martingale Levels:
 Level 1 → {(get_nigeria_time() + timedelta(minutes=6)).strftime('%I:%M %p')}
 Level 2 → {(get_nigeria_time() + timedelta(minutes=9)).strftime('%I:%M %p')}
 Level 3 → {(get_nigeria_time() + timedelta(minutes=12)).strftime('%I:%M %p')}

⏰ {format_time()} (Nigeria Time)
"""
    
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg))
    return jsonify({"status": "sent"}), 200

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    await update.message.reply_text(
        f"🤖 POCKET OPTION TRADING BOT\n\n"
        f"✅ Bot ONLINE\n"
        f"📡 WebSocket: {'✅ CONNECTED' if settings['ws_connected'] else '❌ DISCONNECTED'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n\n"
        f"Commands:\n"
        f"/status - Check status\n"
        f"/webhook - Get webhook URL\n"
        f"/autotrade - Toggle auto trade\n\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['ws_connected'] else '❌ DISCONNECTED'}\n"
        f"🤖 Auto-trade: {'✅ ON' if settings['auto_trade'] else '❌ OFF'}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"📊 Total signals: {settings['total_signals']}\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 WEBHOOK URL\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"Headers:\n"
        f"X-Webhook-Token: {WEBHOOK_SECRET}\n\n"
        f"Example JSON:\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY'}}</code>",
        parse_mode='HTML'
    )

async def autotrade_command(update, context):
    if not settings["ws_connected"]:
        await update.message.reply_text("❌ Pocket Option not connected! Cannot enable auto-trade.")
        return
    
    settings["auto_trade"] = not settings["auto_trade"]
    status = "ON" if settings["auto_trade"] else "OFF"
    await update.message.reply_text(f"🤖 Auto-trade turned {status}\n\n⚠️ Currently in DEMO mode only!")

# Add handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(CommandHandler("webhook", webhook_command))
telegram_app.add_handler(CommandHandler("autotrade", autotrade_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 POCKET OPTION BOT\n\n✅ Bot ONLINE\n📡 Connecting to Pocket Option...\n⏰ {format_time()}"
    )

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

async def main():
    # Send startup message
    await send_startup()
    
    # Start WebSocket connection
    start_websocket()
    
    # Start Flask thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Webhook server started")
    
    # Start Telegram bot
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📍 {format_time()}")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
