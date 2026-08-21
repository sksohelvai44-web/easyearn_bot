import os
import logging
from telegram import Update, ReplyKeyboardMarkup, BotCommand
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
    ["👥 All Users", "📋 All Tasks"],
    ["💳 Pending Withdrawals", "📊 Stats"],
    ["📱 User Menu"]
], resize_keyboard=True)

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMIN_IDS:
        await update.message.reply_text("👋 Welcome Admin!", reply_markup=admin_menu)
    else:
        await update.message.reply_text("👋 Welcome!\nUse the buttons below:", reply_markup=main_menu)

# ==================== HANDLER ====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS

    # ============ CANCEL ============
    if text == "❌ Cancel":
        if is_admin:
            await update.message.reply_text("❌ Cancelled!", reply_markup=admin_menu)
        else:
            await update.message.reply_text("❌ Cancelled!", reply_markup=main_menu)
        return

    # ============ ADMIN ============
    if is_admin:
        if text == "📱 User Menu":
            await update.message.reply_text("📱 User Menu", reply_markup=main_menu)
            return
        if text == "👥 All Users":
            await update.message.reply_text("👥 Total Users: 0", reply_markup=admin_menu)
            return
        if text == "📋 All Tasks":
            await update.message.reply_text("📋 No tasks yet", reply_markup=admin_menu)
            return
        if text == "💳 Pending Withdrawals":
            await update.message.reply_text("💳 No pending withdrawals", reply_markup=admin_menu)
            return
        if text == "📊 Stats":
            await update.message.reply_text("📊 Bot is running!", reply_markup=admin_menu)
            return

    # ============ MAIN MENU ============
    if text == "📋 Task":
        await update.message.reply_text("📋 Task selected!", reply_markup=main_menu)
        return

    if text == "💰 Balance":
        await update.message.reply_text("💰 Your Balance: 0 BDT", reply_markup=main_menu)
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
        await update.message.reply_text("🌐 Select Language:\n\n🇬🇧 English\n🇧🇩 বাংলা", reply_markup=main_menu)
        return

    # ============ UNKNOWN ============
    await update.message.reply_text("❌ Unknown command!", reply_markup=main_menu)

# ==================== MAIN ====================
async def set_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "Start")])

def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = set_commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
