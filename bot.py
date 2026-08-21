import os
import logging
import sqlite3
import random
import string
import pyotp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [7816083990]  # 👈 আপনার আইডি

if not TOKEN:
    logger.error("BOT_TOKEN not set!")
    exit(1)

# ==================== DATABASE ====================
db = sqlite3.connect("taskly.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        balance REAL DEFAULT 0,
        total_earned REAL DEFAULT 0,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        referral_earnings REAL DEFAULT 0,
        language TEXT DEFAULT 'bn',
        is_banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS instagram_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        password TEXT,
        twofa_key TEXT,
        authenticator_code TEXT,
        status TEXT DEFAULT 'pending',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        reward REAL DEFAULT 4.00,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        method TEXT,
        account_number TEXT,
        status TEXT DEFAULT 'pending',
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
db.commit()

def get_user(telegram_id):
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    return cursor.fetchone()

def create_user(telegram_id, username, first_name):
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    is_admin = 1 if telegram_id in ADMIN_IDS else 0
    cursor.execute('''
        INSERT INTO users (telegram_id, username, first_name, referral_code, is_admin)
        VALUES (?, ?, ?, ?, ?)
    ''', (telegram_id, username, first_name, referral_code, is_admin))
    db.commit()
    return get_user(telegram_id)

def add_balance(user_id, amount):
    cursor.execute('''
        UPDATE users SET balance = balance + ?, total_earned = total_earned + ?
        WHERE id = ?
    ''', (amount, amount, user_id))
    db.commit()

def deduct_balance(user_id, amount):
    cursor.execute('''
        UPDATE users SET balance = balance - ?
        WHERE id = ? AND balance >= ?
    ''', (amount, user_id, amount))
    db.commit()

def create_instagram_task(user_id, username, password):
    cursor.execute('''
        INSERT INTO instagram_tasks (user_id, username, password, status, reward)
        VALUES (?, ?, ?, 'pending', 4.00)
    ''', (user_id, username, password))
    db.commit()
    return cursor.lastrowid

def update_instagram_task(task_id, status, twofa_key=None, authenticator_code=None):
    cursor.execute('''
        UPDATE instagram_tasks 
        SET status = ?, twofa_key = ?, authenticator_code = ?, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, twofa_key, authenticator_code, task_id))
    db.commit()

def create_withdrawal(user_id, amount, method, account_number):
    cursor.execute('''
        INSERT INTO withdrawals (user_id, amount, method, account_number, status)
        VALUES (?, ?, ?, ?, 'pending')
    ''', (user_id, amount, method, account_number))
    db.commit()
    return cursor.lastrowid

def get_pending_withdrawals():
    cursor.execute('''
        SELECT w.*, u.username, u.first_name 
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        WHERE w.status = 'pending'
        ORDER BY w.requested_at ASC
    ''')
    return cursor.fetchall()

def get_all_users():
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    return cursor.fetchall()

def get_all_tasks():
    cursor.execute('''
        SELECT t.*, u.username, u.first_name 
        FROM instagram_tasks t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.id DESC
    ''')
    return cursor.fetchall()

def generate_credentials():
    username = "insta_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    password = "P@ss" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return username, password

def generate_authenticator_code(key):
    try:
        totp = pyotp.TOTP(key)
        return totp.now()
    except:
        return None

user_states = {}
withdraw_states = {}

# ==================== INLINE KEYBOARDS ====================

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Task", callback_data="task")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("🔗 Refer", callback_data="refer")],
        [InlineKeyboardButton("🌐 Language", callback_data="language")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def task_menu():
    keyboard = [
        [InlineKeyboardButton("📱 Instagram 2FA", callback_data="insta")],
        [InlineKeyboardButton("📘 Facebook", callback_data="facebook")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def insta_action_menu():
    keyboard = [
        [InlineKeyboardButton("✅ Start", callback_data="insta_start")],
        [InlineKeyboardButton("🎥 Video", callback_data="insta_video")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def insta_cred_menu():
    keyboard = [
        [InlineKeyboardButton("🔐 Set 2FA", callback_data="insta_set_2fa")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def done_menu():
    keyboard = [
        [InlineKeyboardButton("✅ Done", callback_data="insta_done")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def withdraw_menu():
    keyboard = [
        [InlineKeyboardButton("📱 Bkash", callback_data="withdraw_bkash")],
        [InlineKeyboardButton("📱 Nagad", callback_data="withdraw_nagad")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def language_menu():
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    keyboard = [
        [InlineKeyboardButton("👥 All Users", callback_data="admin_users")],
        [InlineKeyboardButton("📋 All Tasks", callback_data="admin_tasks")],
        [InlineKeyboardButton("💳 Pending Withdrawals", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    if not db_user:
        create_user(user.id, user.username or "NoUsername", user.first_name or "User")
        db_user = get_user(user.id)
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n📌 This bot helps you earn money by doing simple tasks.\n✅ Select an option below:",
        reply_markup=main_menu()
    )

# ==================== BUTTON HANDLER ====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    db_user = get_user(user_id)
    
    if not db_user:
        await query.edit_message_text("❌ Please use /start", reply_markup=main_menu())
        return
    
    is_admin = db_user[10] == 1

    # ==================== CANCEL ====================
    if data == "cancel":
        await query.edit_message_text("❌ Cancelled!", reply_markup=main_menu())
        return

    # ==================== ADMIN PANEL ====================
    if data == "admin_panel":
        if is_admin:
            await query.edit_message_text("👑 Admin Panel", reply_markup=admin_menu())
        else:
            await query.edit_message_text("❌ You are not an admin!", reply_markup=main_menu())
        return

    if is_admin:
        if data == "admin_users":
            users = get_all_users()
            if users:
                msg = "👥 All Users:\n\n"
                for u in users[:30]:
                    msg += f"🆔 {u[1]} | @{u[2] or 'N/A'} | Balance: {u[3]:.2f} BDT\n"
                await query.edit_message_text(msg, reply_markup=admin_menu())
            else:
                await query.edit_message_text("No users found.", reply_markup=admin_menu())
            return

        if data == "admin_tasks":
            tasks = get_all_tasks()
            if tasks:
                msg = "📋 All Tasks:\n\n"
                for t in tasks[:20]:
                    msg += f"ID: {t[0]} | User: @{t[9]} | Status: {t[6]} | Reward: {t[7]:.2f} BDT\n"
                await query.edit_message_text(msg, reply_markup=admin_menu())
            else:
                await query.edit_message_text("No tasks found.", reply_markup=admin_menu())
            return

        if data == "admin_withdrawals":
            pending = get_pending_withdrawals()
            if pending:
                msg = "💳 Pending Withdrawals:\n\n"
                for w in pending:
                    msg += f"ID: {w[0]} | @{w[8]} | {w[2]:.2f} BDT | {w[3]}\n"
                await query.edit_message_text(msg, reply_markup=admin_menu())
            else:
                await query.edit_message_text("No pending withdrawals.", reply_markup=admin_menu())
            return

        if data == "admin_stats":
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(balance) FROM users")
            total_balance = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'")
            pending_withdraw = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM instagram_tasks WHERE status = 'pending'")
            pending_tasks = cursor.fetchone()[0]
            await query.edit_message_text(
                f"📊 Bot Statistics:\n\n"
                f"👥 Total Users: {total_users}\n"
                f"💰 Total Balance: {total_balance:.2f} BDT\n"
                f"⏳ Pending Tasks: {pending_tasks}\n"
                f"⏳ Pending Withdrawals: {pending_withdraw}",
                reply_markup=admin_menu()
            )
            return

    # ==================== MAIN MENU ====================
    if data == "task":
        await query.edit_message_text("📋 Select Task:", reply_markup=task_menu())
        return

    if data == "balance":
        await query.edit_message_text(
            f"💰 Your Balance\n\nTotal: {db_user[3]:.2f} BDT\nEarned: {db_user[4]:.2f} BDT",
            reply_markup=main_menu()
        )
        return

    if data == "withdraw":
        if db_user[3] < 50:
            await query.edit_message_text(
                f"❌ Minimum withdrawal is 50 BDT.\nYour Balance: {db_user[3]:.2f} BDT",
                reply_markup=main_menu()
            )
            return
        await query.edit_message_text(
            f"💳 Withdraw Money\n\nBalance: {db_user[3]:.2f} BDT\nMin: 50 BDT\n\nSelect method:",
            reply_markup=withdraw_menu()
        )
        return

    if data == "profile":
        await query.edit_message_text(
            f"👤 Your Profile\n\nID: {user_id}\nUsername: @{db_user[1] or 'N/A'}\nBalance: {db_user[3]:.2f} BDT",
            reply_markup=main_menu()
        )
        return

    if data == "refer":
        await query.edit_message_text(
            f"🔗 Referral Program\n\nEarn 10% commission!\n\nYour link:\nhttps://t.me/easyearnultimate_bot?start=ref_{db_user[6]}\n\nCommission: {db_user[8]:.2f} BDT",
            reply_markup=main_menu()
        )
        return

    if data == "language":
        await query.edit_message_text("🌐 Select Language:", reply_markup=language_menu())
        return

    # ==================== TASK MENU ====================
    if data == "insta":
        user_states[user_id] = {'task': 'instagram'}
        await query.edit_message_text(
            "⏳ Review time: 24 h\n\n"
            "📋 Task: 📱 Create Inst (2FA)\n\n"
            "📄 Description: In this task, you must create a new Inst acc using only a real mobile device.\n"
            "🔐 REQUIRED!\n"
            "You must use the information provided by the Telegram bot to register.\n\n"
            "❗If you use your own information, your application will be REJECTED without verification.\n\n"
            "After registration:\n"
            "👉 No need to send any info\n"
            "✅ Just click the 'Account Registered' button\n\n"
            "⏳ Review time: 24 h",
            reply_markup=insta_action_menu()
        )
        return

    if data == "facebook":
        await query.edit_message_text("📘 Facebook Task\n\n⏳ Coming soon!", reply_markup=task_menu())
        return

    # ==================== INSTAGRAM FLOW ====================
    if data == "insta_start":
        if user_id not in user_states or user_states[user_id].get('task') != 'instagram':
            await query.edit_message_text("❌ Please start task first!", reply_markup=main_menu())
            return

        username, password = generate_credentials()
        task_id = create_instagram_task(db_user[0], username, password)
        user_states[user_id]['task_id'] = task_id
        user_states[user_id]['step'] = 'credentials'

        await query.edit_message_text(
            f"✅ Account Created!\n\n"
            f"👤 Username: {username}\n"
            f"🔑 Password: {password}\n\n"
            f"📌 Please login with these credentials.",
            reply_markup=insta_cred_menu()
        )
        return

    if data == "insta_video":
        await query.edit_message_text(
            "🎥 Tutorial Video:\n\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ",
            reply_markup=insta_action_menu()
        )
        return

    if data == "insta_set_2fa":
        if user_id not in user_states or user_states[user_id].get('step') != 'credentials':
            await query.edit_message_text("❌ No active task!", reply_markup=main_menu())
            return

        user_states[user_id]['step'] = 'waiting_2fa'
        await query.edit_message_text(
            "📱 Enter your 2FA Secret Key:\n\n"
            "Example: JBSWY3DPEHPK3PXP\n\n"
            "_(Send the key)_",
            reply_markup=cancel_menu()
        )
        return

    if data == "insta_done":
        if user_id not in user_states or user_states[user_id].get('step') != 'done':
            await query.edit_message_text("❌ No active task!", reply_markup=main_menu())
            return

        task_id = user_states[user_id]['task_id']
        update_instagram_task(task_id, 'completed')
        add_balance(db_user[0], 4.00)
        user_states.pop(user_id, None)

        await query.edit_message_text(
            "✅ Task Completed!\n\n"
            "💰 +4 BDT added to your balance!",
            reply_markup=main_menu()
        )
        return

    # ==================== WITHDRAW ====================
    if data == "withdraw_bkash":
        withdraw_states[user_id] = {'method': 'Bkash', 'step': 'number'}
        await query.edit_message_text(
            "📱 Enter your Bkash number:\n\nExample: 01XXXXXXXXX",
            reply_markup=cancel_menu()
        )
        return

    if data == "withdraw_nagad":
        withdraw_states[user_id] = {'method': 'Nagad', 'step': 'number'}
        await query.edit_message_text(
            "📱 Enter your Nagad number:\n\nExample: 01XXXXXXXXX",
            reply_markup=cancel_menu()
        )
        return

    # ==================== LANGUAGE ====================
    if data == "lang_en":
        cursor.execute("UPDATE users SET language = 'en' WHERE telegram_id = ?", (user_id,))
        db.commit()
        await query.edit_message_text("✅ Language changed to English!", reply_markup=main_menu())
        return

    if data == "lang_bn":
        cursor.execute("UPDATE users SET language = 'bn' WHERE telegram_id = ?", (user_id,))
        db.commit()
        await query.edit_message_text("✅ ভাষা পরিবর্তন করে বাংলা করা হয়েছে!", reply_markup=main_menu())
        return

    await query.edit_message_text("❌ Unknown command!", reply_markup=main_menu())

# ==================== 2FA KEY MESSAGE HANDLER ====================
async def handle_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states or user_states[user_id].get('step') != 'waiting_2fa':
        await update.message.reply_text("❌ No active task!", reply_markup=main_menu())
        return

    key = text.strip().upper()
    code = generate_authenticator_code(key)

    if code:
        task_id = user_states[user_id]['task_id']
        update_instagram_task(task_id, 'pending', key, code)
        user_states[user_id]['step'] = 'done'

        await update.message.reply_text(
            f"✅ 2FA Key Received!\n\n"
            f"✅ Your verification code: {code}\n\n"
            f"📌 Enter this code in Instagram.\n\n"
            f"Click Done when finished:",
            reply_markup=done_menu()
        )
    else:
        await update.message.reply_text(
            "❌ Invalid 2FA Key! Please try again.",
            reply_markup=cancel_menu()
        )

# ==================== WITHDRAW NUMBER/AMOUNT HANDLER ====================
async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    db_user = get_user(user_id)

    if not db_user:
        await update.message.reply_text("❌ Please use /start", reply_markup=main_menu())
        return

    if user_id not in withdraw_states:
        return

    state = withdraw_states[user_id]

    if state.get('step') == 'number':
        if text.isdigit() and len(text) == 11:
            state['number'] = text
            state['step'] = 'amount'
            await update.message.reply_text(
                f"💰 How much to withdraw?\n\n"
                f"⚠️ Min: 50 BDT\n"
                f"💰 Balance: {db_user[3]:.2f} BDT",
                reply_markup=cancel_menu()
            )
        else:
            await update.message.reply_text("❌ Invalid number! Enter 11 digits.", reply_markup=cancel_menu())
        return

    if state.get('step') == 'amount':
        try:
            amount = float(text)
            if amount < 50 or amount > db_user[3]:
                await update.message.reply_text(
                    f"❌ Invalid amount! Min: 50, Max: {db_user[3]:.2f}",
                    reply_markup=cancel_menu()
                )
                return

            method = state['method']
            number = state['number']
            create_withdrawal(db_user[0], amount, method, number)
            deduct_balance(db_user[0], amount)
            withdraw_states.pop(user_id, None)

            await update.message.reply_text(
                f"✅ Withdrawal Request Submitted!\n\n"
                f"📱 Method: {method}\n"
                f"📞 Number: {number}\n"
                f"💰 Amount: {amount:.2f} BDT\n\n"
                f"⏳ Pending approval.",
                reply_markup=main_menu()
            )
        except:
            await update.message.reply_text("❌ Invalid amount!", reply_markup=cancel_menu())

# ==================== MAIN ====================
async def set_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "🚀 Start")])

def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = set_commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_2fa))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw))
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
