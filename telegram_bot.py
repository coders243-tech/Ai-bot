# Add these methods to your main.py if not already present

def get_status(self):
    po_status = "✅ CONNECTED" if settings["po_connected"] else "❌ DISCONNECTED"
    auto_signal = "✅ ON" if settings["auto_signals_enabled"] else "❌ OFF"
    auto_trade = "✅ ON" if settings["auto_trade_enabled"] else "❌ OFF"
    
    return f"""
📊 <b>BOT STATUS</b>

✅ Status: ONLINE
📡 Pocket Option: {po_status}
🤖 Auto Signals: {auto_signal}
💰 Auto Trade: {auto_trade}
📊 Total Signals: {settings['total_signals']}
📈 Pairs Monitored: {len(config.PRIORITY_PAIRS)}
🌍 Total Instruments: {len(config.ALL_PAIRS)}

⏰ {format_time()} (Nigeria Time)
"""

def get_stats(self):
    return f"""
📊 <b>TRADING STATISTICS</b>

Total Signals: {settings['total_signals']}
Total Trades: {settings['total_trades']}
Auto Signals: {'ON' if settings['auto_signals_enabled'] else 'OFF'}
Auto Trade: {'ON' if settings['auto_trade_enabled'] else 'OFF'}
Pocket Option: {'Connected' if settings['po_connected'] else 'Disconnected'}

⏰ {format_time()} (Nigeria Time)
"""
