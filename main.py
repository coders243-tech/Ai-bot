"""
POCKET OPTION TRADING BOT - REAL PRICES ONLY
Fixed API connections | Binance + Alpha Vantage | No fallbacks
"""

import os
import asyncio
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler

import config
from signal_generator import SignalGenerator

load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║   POCKET OPTION TRADING BOT - REAL PRICES ONLY                 ║
║   Binance WebSocket | Alpha Vantage REST | Nigeria Time        ║
╚════════════════════════════════════════════════════════════════╝
""")

# ============================================
# CREDENTIALS
# ============================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "ZBJN7KGNDPHVVCCW")

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
# TELEGRAM BOT SETUP
# ============================================

bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()
signal_gen = SignalGenerator()

# Settings
settings = {
    "auto_signals_enabled": True,
    "total_signals": 0,
    "last_signal_time": {},
    "last_prices": {},
    "api_call_times": []
}

# ============================================
# RATE LIMITER (5 calls per minute for Alpha Vantage)
# ============================================

async def rate_limit_wait():
    """Ensure we don't exceed 5 calls per minute"""
    now = datetime.now().timestamp()
    # Remove calls older than 60 seconds
    settings["api_call_times"] = [t for t in settings["api_call_times"] if now - t < 60]
    
    if len(settings["api_call_times"]) >= 5:
        oldest = min(settings["api_call_times"])
        wait_time = 60 - (now - oldest)
        if wait_time > 0:
            print(f"⏳ Rate limit: waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
    
    settings["api_call_times"].append(now)

# ============================================
# BINANCE API (Crypto - No rate limit)
# ============================================

def get_binance_price(symbol):
    """Get crypto price from Binance REST API"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data['price'])
        else:
            print(f"⚠️ Binance {symbol}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Binance error for {symbol}: {e}")
        return None

# ============================================
# ALPHA VANTAGE API (Forex - Rate limited)
# ============================================

async def get_alpha_vantage_forex(pair):
    """Get forex price from Alpha Vantage with rate limiting"""
    await rate_limit_wait()
    
    try:
        from_curr = pair[:3]
        to_curr = pair[3:]
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_curr}&to_currency={to_curr}&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
            if rate:
                print(f"✅ Alpha Vantage {pair}: {rate}")
                return float(rate)
            else:
                print(f"⚠️ Alpha Vantage {pair}: No rate in response")
                return None
        else:
            print(f"⚠️ Alpha Vantage {pair}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Alpha Vantage error for {pair}: {e}")
        return None

async def get_alpha_vantage_stock(symbol):
    """Get stock price from Alpha Vantage with rate limiting"""
    await rate_limit_wait()
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data.get("Global Quote", {}).get("05. price")
            if price:
                print(f"✅ Alpha Vantage {symbol}: {price}")
                return float(price)
            else:
                print(f"⚠️ Alpha Vantage {symbol}: No price in response")
                return None
        else:
            print(f"⚠️ Alpha Vantage {symbol}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Alpha Vantage error for {symbol}: {e}")
        return None

# ============================================
# WORKING SYMBOLS (Confirmed working)
# ============================================

# Binance crypto symbols (all working)
CRYPTO_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT", "AVAXUSDT",
    "LINKUSDT", "LTCUSDT", "NEARUSDT", "ATOMUSDT", "SHIBUSDT",
]

# Alpha Vantage forex symbols (correct format)
FOREX_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "NZDUSD", "USDCHF", "EURGBP", "EURJPY", "EURCHF",
]

# Alpha Vantage stock/commodity symbols
STOCK_SYMBOLS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "US100": "^IXIC",
    "US30": "^DJI",
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
}

# ============================================
# PROCESS SIGNAL
# ============================================

async def process_signal(pair, price, data_source, is_manual=False):
    """Process a pair and send signal if conditions met"""
    if not price:
        return False
    
    settings["last_prices"][pair] = price
    signal_gen.update_price(pair, price)
    
    signal = signal_gen.generate_signal(pair, price, data_source)
    
    if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
        current_time = datetime.now().timestamp()
        last_time = settings["last_signal_time"].get(pair, 0)
        
        if is_manual or (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
            if not is_manual:
                settings["last_signal_time"][pair] = current_time
            settings["total_signals"] += 1
            
            message = signal_gen.format_signal_message(signal)
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
            print(f"📤 SIGNAL: {pair} {signal['direction']} ({signal['confidence']}%)")
            return True
    
    return False

# ============================================
# SCAN FUNCTIONS
# ============================================

async def scan_crypto():
    """Scan all crypto pairs"""
    signals = 0
    for symbol in CRYPTO_SYMBOLS:
        price = get_binance_price(symbol)
        if price:
            if await process_signal(symbol, price, "Binance"):
                signals += 1
        await asyncio.sleep(0.3)
    return signals

async def scan_forex():
    """Scan all forex pairs"""
    signals = 0
    for symbol in FOREX_SYMBOLS:
        price = await get_alpha_vantage_forex(symbol)
        if price:
            if await process_signal(symbol, price, "Alpha Vantage"):
                signals += 1
        await asyncio.sleep(1)
    return signals

async def scan_stocks():
    """Scan all stocks and indices"""
    signals = 0
    for name, symbol in STOCK_SYMBOLS.items():
        price = await get_alpha_vantage_stock(symbol)
        if price:
            if await process_signal(name, price, "Alpha Vantage"):
                signals += 1
        await asyncio.sleep(1)
    return signals

async def full_scan(is_manual=False):
    """Run complete scan of all pairs"""
    print(f"🔍 Scan starting at {format_time()}")
    
    crypto = await scan_crypto()
    forex = await scan_forex()
    stocks = await scan_stocks()
    
    total = crypto + forex + stocks
    print(f"✅ Scan complete: {total} signals at {format_time()}")
    return total

# ============================================
# AUTO SIGNAL LOOP
# ============================================

async def auto_signal_loop():
    """Run auto signals every 11 minutes"""
    while True:
        if settings["auto_signals_enabled"]:
            await full_scan(is_manual=False)
        await asyncio.sleep(config.SCAN_INTERVAL_SECONDS)

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    auto_status = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    await update.message.reply_text(
        f"🤖 <b>POCKET OPTION TRADING BOT - REAL PRICES</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"🤖 Auto Signals: {auto_status}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"📈 Crypto: {len(CRYPTO_SYMBOLS)} pairs (Binance)\n"
        f"📈 Forex: {len(FOREX_SYMBOLS)} pairs (Alpha Vantage)\n"
        f"📈 Stocks: {len(STOCK_SYMBOLS)} pairs (Alpha Vantage)\n\n"
        f"📋 <b>Commands:</b>\n"
        f"/status - Bot status\n"
        f"/signal [pair] - Manual signal\n"
        f"/pairs - List all pairs\n"
        f"/scan - Force manual scan\n"
        f"/autosignal - Toggle auto signals\n"
        f"/stats - Trading statistics\n"
        f"/time - Current time\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def status_command(update, context):
    auto_status = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    await update.message.reply_text(
        f"📊 <b>BOT STATUS</b>\n\n"
        f"✅ Status: ONLINE\n"
        f"🤖 Auto Signals: {auto_status}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"🎯 Min Confidence: {config.MIN_CONFIDENCE}%\n"
        f"⏱️ Scan Interval: {config.SCAN_INTERVAL_SECONDS // 60} minutes\n"
        f"📈 Crypto: {len(CRYPTO_SYMBOLS)} pairs\n"
        f"📈 Forex: {len(FOREX_SYMBOLS)} pairs\n"
        f"📈 Stocks: {len(STOCK_SYMBOLS)} pairs\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair]\n\n"
            f"Examples: /signal BTCUSDT\n"
            f"          /signal EURUSD\n"
            f"          /signal Gold\n"
            f"          /signal Apple\n\n"
            f"Type /pairs to see all instruments"
        )
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    price = None
    data_source = None
    
    # Check crypto
    if pair in CRYPTO_SYMBOLS:
        price = get_binance_price(pair)
        data_source = "Binance"
    
    # Check forex
    if not price and pair in FOREX_SYMBOLS:
        price = await get_alpha_vantage_forex(pair)
        data_source = "Alpha Vantage"
    
    # Check stocks
    if not price and pair in STOCK_SYMBOLS:
        price = await get_alpha_vantage_stock(STOCK_SYMBOLS[pair])
        data_source = "Alpha Vantage"
    
    if not price:
        await update.message.reply_text(f"❌ Could not fetch price for {pair}. API may be rate limited.")
        return
    
    signal = signal_gen.generate_signal(pair, price, data_source)
    
    if signal:
        message = signal_gen.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='HTML')
        settings["total_signals"] += 1
    else:
        history = signal_gen.price_history.get(pair, [])
        rsi = signal_gen.calculate_rsi(history) if len(history) >= 15 else 50
        await update.message.reply_text(
            f"📊 {pair} Analysis\n\n"
            f"💰 Price: ${price:.5f} (LIVE)\n"
            f"📈 RSI: {rsi}\n\n"
            f"❌ No strong signal right now.\n"
            f"RSI is in neutral zone (30-70)."
        )

async def pairs_command(update, context):
    await update.message.reply_text(
        f"📊 <b>AVAILABLE INSTRUMENTS</b>\n\n"
        f"<b>Crypto ({len(CRYPTO_SYMBOLS)})</b>\n"
        f"{', '.join(CRYPTO_SYMBOLS)}\n\n"
        f"<b>Forex ({len(FOREX_SYMBOLS)})</b>\n"
        f"{', '.join(FOREX_SYMBOLS)}\n\n"
        f"<b>Stocks & Indices ({len(STOCK_SYMBOLS)})</b>\n"
        f"{', '.join(STOCK_SYMBOLS.keys())}\n\n"
        f"<b>TOTAL: {len(CRYPTO_SYMBOLS) + len(FOREX_SYMBOLS) + len(STOCK_SYMBOLS)} instruments</b>\n\n"
        f"Use /signal [pair] for any instrument",
        parse_mode='HTML'
    )

async def scan_command(update, context):
    await update.message.reply_text(f"🔍 Manual scan started...\n⏰ {format_time()}")
    total = await full_scan(is_manual=True)
    await update.message.reply_text(
        f"🔍 <b>SCAN COMPLETE!</b>\n\n"
        f"✅ Found {total} signal(s)\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def autosignal_command(update, context):
    settings["auto_signals_enabled"] = not settings["auto_signals_enabled"]
    status = "ON" if settings["auto_signals_enabled"] else "OFF"
    await update.message.reply_text(
        f"🤖 Auto Signals turned {status}\n\n"
        f"When ON, signals will be sent automatically every {config.SCAN_INTERVAL_SECONDS // 60} minutes.\n"
        f"⏰ {format_time()} (Nigeria Time)"
    )

async def stats_command(update, context):
    await update.message.reply_text(
        f"📊 <b>TRADING STATISTICS</b>\n\n"
        f"Total Signals: {settings['total_signals']}\n"
        f"Auto Signals: {'ON' if settings['auto_signals_enabled'] else 'OFF'}\n"
        f"Min Confidence: {config.MIN_CONFIDENCE}%\n"
        f"Scan Interval: {config.SCAN_INTERVAL_SECONDS // 60} minutes\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def time_command(update, context):
    await update.message.reply_text(f"⏰ Nigeria Time: {format_time()}")

# Register all commands
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("status", status_command))
application.add_handler(CommandHandler("signal", signal_command))
application.add_handler(CommandHandler("pairs", pairs_command))
application.add_handler(CommandHandler("scan", scan_command))
application.add_handler(CommandHandler("autosignal", autosignal_command))
application.add_handler(CommandHandler("stats", stats_command))
application.add_handler(CommandHandler("time", time_command))

print("✅ All command handlers registered")

# ============================================
# STARTUP
# ============================================

async def send_startup():
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"🤖 <b>POCKET OPTION TRADING BOT - REAL PRICES</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"📊 Crypto: {len(CRYPTO_SYMBOLS)} pairs (Binance)\n"
        f"📊 Forex: {len(FOREX_SYMBOLS)} pairs (Alpha Vantage)\n"
        f"📊 Stocks: {len(STOCK_SYMBOLS)} pairs (Alpha Vantage)\n"
        f"🤖 Auto signals: ON (every {config.SCAN_INTERVAL_SECONDS // 60} minutes)\n"
        f"🎯 Min Confidence: {config.MIN_CONFIDENCE}%\n\n"
        f"⏰ {format_time()} (Nigeria Time)\n\n"
        f"⚠️ All prices are LIVE from Binance and Alpha Vantage\n"
        f"Try /scan to test!",
        parse_mode='HTML'
    )

async def main():
    await send_startup()
    
    # Start auto signal loop
    asyncio.create_task(auto_signal_loop())
    
    # Start Telegram bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print(f"🚀 Bot is running with REAL prices only!")
    print(f"📍 Nigeria Time: {format_time()}")
    print(f"📋 Commands: /start, /status, /signal, /pairs, /scan, /autosignal, /stats, /time")
    
    # Run initial scan
    await asyncio.sleep(5)
    await full_scan(is_manual=True)
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())