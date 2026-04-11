"""
POCKET OPTION TRADING BOT - COMPLETE VERSION
Real-time signals | All currency pairs | Nigeria Time
"""

import os
import asyncio
import threading
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Pocket Option library
from pocket_option import PocketOptionClient
from pocket_option.constants import Regions

import config
from signal_generator import SignalGenerator
from telegram_bot import TelegramBotHandler

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - COMPLETE VERSION                 ║
║   Real-time signals | All pairs | Nigeria Time                 ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_secret_key_here")
PO_SESSION = os.getenv("PO_SESSION", "0d3ef4dafc05966efc12800ba7963e78")
PO_UID = os.getenv("PO_UID", "29984823")

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
# BOT SETUP
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()
signal_gen = SignalGenerator()

# Settings
settings = {
    "po_connected": False,
    "auto_signals_enabled": True,
    "total_signals": 0,
    "last_price": {},
    "last_rsi": {},
    "last_signal_time": {}
}

# Flask app for webhook
flask_app = Flask(__name__)

# ============================================
# POCKET OPTION CLIENT (REAL-TIME DATA)
# ============================================

po_client = PocketOptionClient()

@po_client.on.connect
async def on_connect(data):
    print("✅ WebSocket connected to Pocket Option!")
    
    # Send authentication
    await po_client.emit.auth(
        session=PO_SESSION,
        isDemo=1,
        uid=int(PO_UID),
        platform=2
    )

@po_client.on.success_auth
async def on_success_auth(data):
    print(f"✅ Authenticated! User ID: {data.id}")
    settings["po_connected"] = True
    
    # Subscribe to all currency pairs
    for pair in config.ALL_PAIRS[:50]:  # First 50 pairs to avoid overload
        otc_pair = f"{pair}{config.OTC_SUFFIX}" if "_otc" not in pair else pair
        await po_client.emit.subscribe_to_asset(otc_pair)
        await asyncio.sleep(0.5)
    
    print(f"📊 Subscribed to {len(config.ALL_PAIRS)} pairs")
    
    # Notify Telegram
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"✅ Pocket Option CONNECTED!\n📊 Monitoring {len(config.ALL_PAIRS)} pairs\n⏰ {format_time()}"
    )

@po_client.on.update_close_value
async def on_price_update(assets):
    """Called for every price update - REAL-TIME!"""
    if not settings["auto_signals_enabled"]:
        return
    
    for asset in assets:
        pair = asset.id.replace("_otc", "")
        price = asset.close_value
        timestamp = asset.time
        
        # Store price
        settings["last_price"][pair] = price
        
        # Generate signal based on price
        signal = signal_gen.generate_signal_from_price(pair, price)
        
        if signal and signal.get("confidence", 0) >= 50:
            current_time = datetime.now().timestamp()
            last_time = settings["last_signal_time"].get(pair, 0)
            
            # Prevent duplicate signals (5 minute cooldown)
            if (current_time - last_time) > 300:
                settings["last_signal_time"][pair] = current_time
                settings["total_signals"] += 1
                
                message = signal_gen.format_signal_message(signal)
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                print(f"📤 AUTO SIGNAL: {pair} {signal['direction']} (Confidence: {signal['confidence']}%)")

@po_client.on.disconnect
async def on_disconnect():
    print("🔌 Disconnected from Pocket Option")
    settings["po_connected"] = False

async def connect_pocket_option():
    """Start Pocket Option connection"""
    try:
        await po_client.connect(Regions.DEMO)
        print("🚀 Pocket Option client started")
    except Exception as e:
        print(f"❌ Connection error: {e}")

# ============================================
# FLASK WEBHOOK (TradingView)
# ============================================

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
    
    martingale = []
    for i in range(1, 4):
        level_time = entry_time + timedelta(minutes=i * 3)
        martingale.append(f" Level {i} → {level_time.strftime('%I:%M %p')}")
    
    msg = f"""
🔔 TRADINGVIEW SIGNAL

🎫 Trade: {symbol}
📈 Direction: {side}
💰 Price: ${price if price > 0 else 'Market'}
⏳ Timer: 3 minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}

↪️ Martingale Levels:
{chr(10).join(martingale)}

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
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['po_connected'] else '🔄 CONNECTING...'}\n"
        f"🤖 Auto signals: {'✅ ON' if settings['auto_signals_enabled'] else '❌ OFF'}\n"
        f"📊 Total signals: {settings['total_signals']}\n\n"
        f"📋 Commands:\n"
        f"/status - Bot status\n"
        f"/signal [pair] - Manual signal\n"
        f"/pairs - List all pairs\n"
        f"/webhook - TradingView webhook URL\n"
        f"/stop - Stop auto signals\n"
        f"/startbot - Start auto signals\n"
        f"/time - Show time\n\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def status_command(update, context):
    await update.message.reply_text(
        f"📊 BOT STATUS\n\n"
        f"✅ Status: ONLINE\n"
        f"📡 Pocket Option: {'✅ CONNECTED' if settings['po_connected'] else '❌ DISCONNECTED'}\n"
        f"🤖 Auto signals: {'✅ ON' if settings['auto_signals_enabled'] else '❌ OFF'}\n"
        f"📊 Total signals: {settings['total_signals']}\n"
        f"🔗 TradingView Webhook: ACTIVE\n"
        f"📈 Pairs monitored: {len(config.ALL_PAIRS)}\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /signal EURUSD\n\nExample: /signal EURUSD")
        return
    
    pair = context.args[0].upper()
    
    # Remove _otc if present
    pair = pair.replace("_OTC", "")
    
    if pair not in config.ALL_PAIRS:
        await update.message.reply_text(f"❌ '{pair}' not found.\n\nType /pairs to see all instruments.")
        return
    
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    price = settings["last_price"].get(pair, 0)
    if price == 0:
        price = 1.09234  # Fallback
    
    signal = signal_gen.generate_signal_from_price(pair, price)
    
    if signal:
        message = signal_gen.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text(f"📊 {pair}: No strong signal right now.\n\nRSI is in neutral zone.")

async def pairs_command(update, context):
    forex = [p for p in config.ALL_PAIRS if p in config.FOREX_PAIRS or p in config.OTC_PAIRS]
    indices = [p for p in config.ALL_PAIRS if p in config.INDICES or p in config.INDICES_OTC]
    commodities = [p for p in config.ALL_PAIRS if p in config.COMMODITIES or p in config.COMMODITIES_OTC]
    crypto = [p for p in config.ALL_PAIRS if p in config.CRYPTOS or p in config.CRYPTOS_OTC]
    stocks = [p for p in config.ALL_PAIRS if p in config.STOCKS or p in config.STOCKS_OTC]
    
    await update.message.reply_text(
        f"📊 AVAILABLE INSTRUMENTS\n\n"
        f"Forex ({len(forex)}): {', '.join(forex[:15])}{'...' if len(forex) > 15 else ''}\n\n"
        f"Indices ({len(indices)}): {', '.join(indices[:10])}{'...' if len(indices) > 10 else ''}\n\n"
        f"Commodities ({len(commodities)}): {', '.join(commodities)}\n\n"
        f"Crypto ({len(crypto)}): {', '.join(crypto[:10])}{'...' if len(crypto) > 10 else ''}\n\n"
        f"Stocks ({len(stocks)}): {', '.join(stocks[:15])}{'...' if len(stocks) > 15 else ''}\n\n"
        f"TOTAL: {len(config.ALL_PAIRS)} instruments\n\n"
        f"Use /signal [pair] for any instrument"
    )

async def webhook_command(update, context):
    railway_url = os.getenv('RAILWAY_PUBLIC_URL', 'https://your-app.railway.app')
    webhook_url = f"{railway_url}/webhook"
    
    await update.message.reply_text(
        f"🔗 WEBHOOK URL\n\n"
        f"<code>{webhook_url}</code>\n\n"
        f"Headers:\n"
        f"X-Webhook-Token: {WEBHOOK_SECRET}\n\n"
        f"JSON Example:\n"
        f"<code>{{'symbol': 'EURUSD', 'side': 'BUY', 'price': 1.09234}}</code>\n\n"
        f"Text Example:\n"
        f"BUY EURUSD at 1.09234",
        parse_mode='HTML'
    )

async def stop_command(update, context):
    settings["auto_signals_enabled"] = False
    await update.message.reply_text(f"🛑 Auto signals STOPPED\n\nManual /signal still works.\nUse /startbot to resume.\n\n⏰ {format_time()}")

async def startbot_command(update, context):
    settings["auto_signals_enabled"] = True
    await update.message.reply_text(f"✅ Auto signals RESUMED!\n\nSignals will be sent automatically.\n\n⏰ {format_time()}")

async def time_command(update, context):
    await update.message.reply_text(f"⏰ Nigeria Time: {format_time()}")

# Add handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("webhook", webhook_command))
application.add_handler(CommandHandler("stop", stop_command))
application.add_handler(CommandHandler("startbot", startbot_command))
application.add_handler(CommandHandler("time", time_command))

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 POCKET OPTION BOT\n\n✅ Bot ONLINE!\n📡 Connecting to Pocket Option...\n📊 Pairs: {len(config.ALL_PAIRS)}\n\n⏰ {format_time()}"
    )

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

async def main():
    await send_startup()
    
    # Start Pocket Option connection
    asyncio.create_task(connect_pocket_option())
    
    # Start Flask thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🚀 Webhook server started")
    
    # Start Telegram bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🚀 Telegram bot started")
    print(f"📍 Nigeria Time: {format_time()}")
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
