"""
POCKET OPTION TRADING BOT - CORRECTED VERSION
Simplified price fetching | Binance REST API | Alpha Vantage
"""

import os
import asyncio
import aiohttp
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
║   POCKET OPTION TRADING BOT - CORRECTED VERSION                ║
║   Simplified price fetching | Binance REST | Alpha Vantage     ║
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
    "last_prices": {}
}

# ============================================
# PRICE FETCHING FUNCTIONS
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
            print(f"Binance error for {symbol}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Binance exception for {symbol}: {e}")
        return None

def get_alpha_vantage_forex(from_currency, to_currency):
    """Get forex price from Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
            if rate:
                return float(rate)
        return None
    except Exception as e:
        print(f"Alpha Vantage forex error: {e}")
        return None

def get_alpha_vantage_price(symbol):
    """Get stock/commodity/index price from Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get("Global Quote", {}).get("05. price")
            if price:
                return float(price)
        return None
    except Exception as e:
        print(f"Alpha Vantage price error: {e}")
        return None

# ============================================
# FALLBACK PRICES (When APIs fail)
# ============================================

FALLBACK_PRICES = {
    "BTCUSDT": 65000.00,
    "ETHUSDT": 3500.00,
    "EURUSD": 1.09234,
    "GBPUSD": 1.28560,
    "USDJPY": 148.50,
    "Gold": 2350.00,
    "Silver": 28.50,
    "US100": 18500.00,
    "Apple": 175.00,
    "Tesla": 240.00,
}

def get_fallback_price(pair):
    """Return fallback price if available"""
    return FALLBACK_PRICES.get(pair, None)

# ============================================
# SIGNAL SCANNER
# ============================================

async def scan_and_send_signals(is_manual=False):
    """Scan all pairs and send signals"""
    signals_found = 0
    results = []
    
    # 1. Scan Crypto (Binance)
    for pair in config.CRYPTO_PAIRS[:20]:  # Limit to 20 for speed
        price = get_binance_price(pair)
        if not price:
            price = get_fallback_price(pair)
        
        if price:
            settings["last_prices"][pair] = price
            signal = signal_gen.generate_signal(pair, price, "Binance")
            
            if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
                current_time = datetime.now().timestamp()
                last_time = settings["last_signal_time"].get(pair, 0)
                
                if is_manual or (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
                    if not is_manual:
                        settings["last_signal_time"][pair] = current_time
                    settings["total_signals"] += 1
                    signals_found += 1
                    
                    message = signal_gen.format_signal_message(signal)
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                    print(f"📤 SIGNAL: {pair} {signal['direction']}")
                    results.append(f"• {signal['direction']} {pair}")
        
        await asyncio.sleep(0.5)  # Small delay
    
    # 2. Scan Forex Majors
    for pair, symbol in config.FOREX_MAJORS.items():
        from_curr = symbol[:3]
        to_curr = symbol[3:]
        price = get_alpha_vantage_forex(from_curr, to_curr)
        if not price:
            price = get_fallback_price(pair)
        
        if price:
            settings["last_prices"][pair] = price
            signal = signal_gen.generate_signal(pair, price, "Alpha Vantage")
            
            if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
                current_time = datetime.now().timestamp()
                last_time = settings["last_signal_time"].get(pair, 0)
                
                if is_manual or (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
                    if not is_manual:
                        settings["last_signal_time"][pair] = current_time
                    settings["total_signals"] += 1
                    signals_found += 1
                    
                    message = signal_gen.format_signal_message(signal)
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                    print(f"📤 SIGNAL: {pair} {signal['direction']}")
                    results.append(f"• {signal['direction']} {pair}")
        
        await asyncio.sleep(12)  # Alpha Vantage rate limit
    
    # 3. Scan Forex Minors
    for pair, symbol in config.FOREX_MINORS.items():
        from_curr = symbol[:3]
        to_curr = symbol[3:]
        price = get_alpha_vantage_forex(from_curr, to_curr)
        
        if price:
            settings["last_prices"][pair] = price
            signal = signal_gen.generate_signal(pair, price, "Alpha Vantage")
            
            if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
                current_time = datetime.now().timestamp()
                last_time = settings["last_signal_time"].get(pair, 0)
                
                if is_manual or (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
                    if not is_manual:
                        settings["last_signal_time"][pair] = current_time
                    settings["total_signals"] += 1
                    signals_found += 1
                    
                    message = signal_gen.format_signal_message(signal)
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                    print(f"📤 SIGNAL: {pair} {signal['direction']}")
                    results.append(f"• {signal['direction']} {pair}")
        
        await asyncio.sleep(12)
    
    # 4. Scan Indices, Commodities, Stocks (simplified)
    all_others = {**config.INDICES, **config.COMMODITIES, **config.STOCKS}
    for pair, symbol in list(all_others.items())[:15]:  # Limit to 15
        price = get_alpha_vantage_price(symbol)
        if not price:
            price = get_fallback_price(pair)
        
        if price:
            settings["last_prices"][pair] = price
            signal = signal_gen.generate_signal(pair, price, "Alpha Vantage")
            
            if signal and signal.get("confidence", 0) >= config.MIN_CONFIDENCE:
                current_time = datetime.now().timestamp()
                last_time = settings["last_signal_time"].get(pair, 0)
                
                if is_manual or (current_time - last_time) > config.SIGNAL_COOLDOWN_SECONDS:
                    if not is_manual:
                        settings["last_signal_time"][pair] = current_time
                    settings["total_signals"] += 1
                    signals_found += 1
                    
                    message = signal_gen.format_signal_message(signal)
                    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
                    print(f"📤 SIGNAL: {pair} {signal['direction']}")
                    results.append(f"• {signal['direction']} {pair}")
        
        await asyncio.sleep(12)
    
    return signals_found, results

# ============================================
# AUTO SIGNAL LOOP
# ============================================

async def auto_signal_loop():
    """Run auto signals every 11 minutes"""
    while True:
        if settings["auto_signals_enabled"]:
            print(f"🔍 Auto scan starting at {format_time()}")
            signals_found, _ = await scan_and_send_signals(is_manual=False)
            print(f"✅ Auto scan complete. Found {signals_found} signals at {format_time()}")
        
        await asyncio.sleep(config.SCAN_INTERVAL_SECONDS)

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start_command(update, context):
    auto_status = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    await update.message.reply_text(
        f"🤖 <b>POCKET OPTION TRADING BOT</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"🤖 Auto Signals: {auto_status}\n"
        f"📊 Total Signals: {settings['total_signals']}\n"
        f"📈 Crypto: {len(config.CRYPTO_PAIRS)} pairs\n"
        f"📈 Forex: {len(config.FOREX_MAJORS) + len(config.FOREX_MINORS)} pairs\n"
        f"📈 Indices: {len(config.INDICES)}\n"
        f"📈 Commodities: {len(config.COMMODITIES)}\n"
        f"📈 Stocks: {len(config.STOCKS)}\n\n"
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
        f"📈 Crypto: {len(config.CRYPTO_PAIRS)} pairs\n"
        f"📈 Forex Majors: {len(config.FOREX_MAJORS)}\n"
        f"📈 Forex Minors: {len(config.FOREX_MINORS)}\n"
        f"📈 Indices: {len(config.INDICES)}\n"
        f"📈 Commodities: {len(config.COMMODITIES)}\n"
        f"📈 Stocks: {len(config.STOCKS)}\n\n"
        f"⏰ {format_time()} (Nigeria Time)",
        parse_mode='HTML'
    )

async def signal_command(update, context):
    if not context.args:
        await update.message.reply_text(
            f"⚠️ Usage: /signal [pair]\n\n"
            f"Examples: /signal BTCUSDT\n"
            f"          /signal EURUSD\n"
            f"          /signal Gold\n\n"
            f"Type /pairs to see all instruments"
        )
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    price = None
    data_source = None
    
    # Try Binance for crypto
    if pair in config.CRYPTO_PAIRS:
        price = get_binance_price(pair)
        data_source = "Binance"
    
    # Try Alpha Vantage for forex
    if not price and pair in config.FOREX_MAJORS:
        symbol = config.FOREX_MAJORS[pair]
        from_curr = symbol[:3]
        to_curr = symbol[3:]
        price = get_alpha_vantage_forex(from_curr, to_curr)
        data_source = "Alpha Vantage"
    
    if not price and pair in config.FOREX_MINORS:
        symbol = config.FOREX_MINORS[pair]
        from_curr = symbol[:3]
        to_curr = symbol[3:]
        price = get_alpha_vantage_forex(from_curr, to_curr)
        data_source = "Alpha Vantage"
    
    # Try fallback price
    if not price:
        price = get_fallback_price(pair)
        data_source = "Fallback"
    
    if not price:
        await update.message.reply_text(f"❌ Could not fetch price for {pair}.")
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
            f"💰 Price: ${price:.5f}\n"
            f"📈 RSI: {rsi}\n\n"
            f"❌ No strong signal right now.\n"
            f"RSI is in neutral zone (30-70).\n\n"
            f"💡 Try /confidence {config.MIN_CONFIDENCE - 5} for more signals"
        )

async def pairs_command(update, context):
    await update.message.reply_text(
        f"📊 <b>AVAILABLE INSTRUMENTS</b>\n\n"
        f"<b>Crypto ({len(config.CRYPTO_PAIRS)})</b>\n"
        f"{', '.join(config.CRYPTO_PAIRS[:15])}...\n\n"
        f"<b>Forex Majors ({len(config.FOREX_MAJORS)})</b>\n"
        f"{', '.join(config.FOREX_MAJORS.keys())}\n\n"
        f"<b>Forex Minors ({len(config.FOREX_MINORS)})</b>\n"
        f"{', '.join(list(config.FOREX_MINORS.keys())[:10])}...\n\n"
        f"<b>Indices ({len(config.INDICES)})</b>\n"
        f"{', '.join(config.INDICES.keys())}\n\n"
        f"<b>Commodities ({len(config.COMMODITIES)})</b>\n"
        f"{', '.join(config.COMMODITIES.keys())}\n\n"
        f"<b>Stocks ({len(config.STOCKS)})</b>\n"
        f"{', '.join(config.STOCKS.keys())}\n\n"
        f"<b>TOTAL: {len(config.CRYPTO_PAIRS) + len(config.FOREX_MAJORS) + len(config.FOREX_MINORS) + len(config.INDICES) + len(config.COMMODITIES) + len(config.STOCKS)} instruments</b>\n\n"
        f"Use /signal [pair] for any instrument",
        parse_mode='HTML'
    )

async def scan_command(update, context):
    await update.message.reply_text(f"🔍 Manual scan started...\n⏰ {format_time()}")
    
    signals_found, results = await scan_and_send_signals(is_manual=True)
    
    if signals_found > 0:
        await update.message.reply_text(
            f"🔍 <b>SCAN COMPLETE!</b>\n\n"
            f"✅ Found {signals_found} signal(s):\n"
            f"{chr(10).join(results)}\n\n"
            f"⏰ {format_time()} (Nigeria Time)",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"🔍 <b>SCAN COMPLETE!</b>\n\n"
            f"❌ No signals found.\n\n"
            f"💡 Try /confidence {config.MIN_CONFIDENCE - 5} for more signals\n"
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
        text=f"🤖 <b>POCKET OPTION TRADING BOT - CORRECTED</b>\n\n"
        f"✅ Bot ONLINE\n"
        f"📊 Crypto: {len(config.CRYPTO_PAIRS)} pairs (Binance REST)\n"
        f"📊 Forex/Stocks: {len(config.FOREX_MAJORS) + len(config.FOREX_MINORS) + len(config.INDICES) + len(config.COMMODITIES) + len(config.STOCKS)} pairs\n"
        f"🤖 Auto signals: ON (every {config.SCAN_INTERVAL_SECONDS // 60} minutes)\n"
        f"🎯 Min Confidence: {config.MIN_CONFIDENCE}%\n\n"
        f"⏰ {format_time()} (Nigeria Time)\n\n"
        f"Try /signal BTCUSDT to test!",
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
    
    print(f"🚀 Bot is running!")
    print(f"📍 Nigeria Time: {format_time()}")
    print(f"📋 Commands: /start, /status, /signal, /pairs, /scan, /autosignal, /stats, /time")
    
    # Send a test signal immediately
    await asyncio.sleep(5)
    print("🔍 Running initial scan...")
    asyncio.create_task(scan_and_send_signals(is_manual=True))
    
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())