import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [7816083990]

if not TOKEN:
    logger.error("BOT_TOKEN not set!")
    exit(1)

# ==================== KEYBOARDS ====================
main_menu = ReplyKeyboardMarkup([
    ["📋 Task", "💰 Balance"],
    ["💳 Withdraw", "👤 Profile"],
    ["🔗 Refer", "🌐 Language"]
], resize_keyboard=True)

admin_menu = ReplyKeyboardMarkup([
    ["👥 All Users", "📊 Stats"],
    ["❌ Cancel"]
], resize_keyboard=True)

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Check if admin
    if user_id in ADMIN_IDS:
        await update.message.reply_text(
            f"👋 Welcome Admin {user.first_name}!\n\nYou have admin access.",
            reply_markup=admin_menu
        )
    else:
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\nUse the buttons below:",
            reply_markup=main_menu
        )

# ==================== MESSAGE HANDLER ====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # Cancel
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled!", reply_markup=main_menu)
        return
    
    # Admin panel
    if user_id in ADMIN_IDS:
        if text == "👥 All Users":
            await update.message.reply_text("👥 Total Users: 0", reply_markup=admin_menu)
            return
        if text == "📊 Stats":
            await update.message.reply_text("📊 Bot is running!", reply_markup=admin_menu)
            return
    
    # Main menu
    if text == "📋 Task":
        await update.message.reply_text("📋 Task selected!", reply_markup=main_menu)
        return
    if text == "💰 Balance":
        await update.message.reply_text("💰 Balance: 0 BDT", reply_markup=main_menu)
        return
    if text == "💳 Withdraw":
        await update.message.reply_text("💳 Withdraw selected!", reply_markup=main_menu)
        return
    if text == "👤 Profile":
        await update.message.reply_text(f"👤 User ID: {user_id}", reply_markup=main_menu)
        return
    if text == "🔗 Refer":
        await update.message.reply_text("🔗 Referral link: https://t.me/yourbot", reply_markup=main_menu)
        return
    if text == "🌐 Language":
        await update.message.reply_text("🌐 Language: English", reply_markup=main_menu)
        return
    
    await update.message.reply_text("❌ Unknown!", reply_markup=main_menu)

# ==================== MAIN ====================
async def set_commands(app):
    commands = [BotCommand("start", "Start")]
    await app.bot.set_my_commands(commands)

def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = set_commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
