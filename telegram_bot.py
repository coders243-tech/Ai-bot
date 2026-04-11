"""
Telegram Bot Handler - Command processing
"""

from telegram import Update
from telegram.ext import ContextTypes

class TelegramBotHandler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.settings = bot_instance.settings if hasattr(bot_instance, 'settings') else {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"🤖 Pocket Option Bot\n\n"
            f"✅ Bot ONLINE\n"
            f"Commands: /status, /signal, /pairs, /webhook, /stop, /startbot"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"📋 COMMANDS\n\n"
            f"/status - Bot status\n"
            f"/signal [pair] - Manual signal\n"
            f"/pairs - List all pairs\n"
            f"/webhook - TradingView webhook URL\n"
            f"/stop - Stop auto signals\n"
            f"/startbot - Start auto signals"
        )
