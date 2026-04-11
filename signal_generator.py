"""
Signal Generator - Real-time RSI calculation and signal formatting
"""

from datetime import datetime, timedelta
import config

class SignalGenerator:
    def __init__(self):
        self.last_prices = {}
        self.last_rsi = {}
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI from price list"""
        if len(prices) < period:
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
        
        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 1)
    
    def generate_signal_from_price(self, pair, price):
        """Generate signal based on price and RSI calculation"""
        # Store price history
        if pair not in self.last_prices:
            self.last_prices[pair] = []
        
        self.last_prices[pair].append(price)
        
        # Keep last 20 prices for RSI calculation
        if len(self.last_prices[pair]) > 20:
            self.last_prices[pair] = self.last_prices[pair][-20:]
        
        # Calculate RSI
        if len(self.last_prices[pair]) >= 14:
            rsi = self.calculate_rsi(self.last_prices[pair])
        else:
            rsi = 50
        
        self.last_rsi[pair] = rsi
        
        # Generate signal based on RSI
        if rsi <= config.RSI_OVERSOLD:
            direction = "BUY"
            confidence = min(95, int(75 - rsi + 20))
            reason = f"RSI Oversold ({rsi}) - Price may reverse UP"
            emoji = "🟢🟢" if confidence >= 75 else "🟢"
        elif rsi >= config.RSI_OVERBOUGHT:
            direction = "SELL"
            confidence = min(95, int(rsi - 70 + 20))
            reason = f"RSI Overbought ({rsi}) - Price may reverse DOWN"
            emoji = "🔴🔴" if confidence >= 75 else "🔴"
        else:
            return None
        
        return {
            'pair': pair,
            'flag': config.get_flag(pair),
            'price': price,
            'rsi': rsi,
            'direction': direction,
            'confidence': confidence,
            'emoji': emoji,
            'reason': reason,
            'timestamp': datetime.now().strftime("%I:%M %p")
        }
    
    def format_signal_message(self, signal):
        """Format signal with 3-minute head start and martingale levels"""
        entry_time = datetime.now() + timedelta(minutes=config.SIGNAL_TIMER_MINUTES)
        
        martingale_lines = []
        for i in range(1, config.MARTINGALE_LEVELS + 1):
            level_time = entry_time + timedelta(minutes=i * config.MARTINGALE_INTERVAL)
            martingale_lines.append(f" Level {i} → {level_time.strftime('%I:%M %p')}")
        
        tp_mult = 1.005 if signal['direction'] == "BUY" else 0.995
        sl_mult = 0.995 if signal['direction'] == "BUY" else 1.005
        
        tp = signal['price'] * tp_mult
        sl = signal['price'] * sl_mult
        
        return f"""
🔔 <b>NEW SIGNAL!</b>

🎫 Trade: {signal['flag']} {signal['pair']} (OTC)
⏳ Timer: {config.SIGNAL_TIMER_MINUTES} minutes
➡️ Entry: {entry_time.strftime('%I:%M %p')}
📈 Direction: {signal['direction']} {signal['emoji']}

💪 <b>Confidence:</b> {signal['confidence']}%

📊 <b>Technical Analysis:</b>
• RSI: {signal['rsi']}
• {signal['reason']}

↪️ <b>Martingale Levels:</b>
{chr(10).join(martingale_lines)}

💰 <b>Entry Price:</b> ${signal['price']:.5f}
🎯 <b>Take Profit:</b> ${tp:.5f}
🛑 <b>Stop Loss:</b> ${sl:.5f}

⏰ {signal['timestamp']} (Nigeria Time)
"""
