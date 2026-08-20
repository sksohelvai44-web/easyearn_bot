import os
import logging
import sqlite3
import random
import string
import pyotp
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [7816083990]  # 👈 আপনার আইডি

if not TOKEN:
    logger.error("BOT_TOKEN not set!")
    exit(1)

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

cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        commission REAL DEFAULT 0,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referrer_id) REFERENCES users (id),
        FOREIGN KEY (referred_id) REFERENCES users (id)
    )
''')
db.commit()

def get_user(telegram_id):
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    return cursor.fetchone()

def create_user(telegram_id, username, first_name, referred_by=None):
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    is_admin = 1 if telegram_id in ADMIN_IDS else 0
    cursor.execute('''
        INSERT INTO users (telegram_id, username, first_name, referral_code, referred_by, is_admin)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (telegram_id, username, first_name, referral_code, referred_by, is_admin))
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

# ==================== KEYBOARDS ====================

main_menu = ReplyKeyboardMarkup([
    ["📋 Task", "💰 Balance"],
    ["💳 Withdraw", "👤 Profile"],
    ["🔗 Refer", "🌐 Language"]
], resize_keyboard=True)

task_menu = ReplyKeyboardMarkup([
    ["📱 Insta 2FA 4 BDT", "📘 Facebook"],
    ["❌ Cancel"]
], resize_keyboard=True)

insta_menu = ReplyKeyboardMarkup([
    ["✅ Start", "🎥 Video"],
    ["❌ Cancel"]
], resize_keyboard=True)

insta_actions = ReplyKeyboardMarkup([
    ["🔐 Set 2FA"],
    ["❌ Cancel"]
], resize_keyboard=True)

done_menu = ReplyKeyboardMarkup([
    ["✅ Done"],
    ["❌ Cancel"]
], resize_keyboard=True)

withdraw_menu = ReplyKeyboardMarkup([
    ["📱 Bkash", "📱 Nagad"],
    ["❌ Cancel"]
], resize_keyboard=True)

language_menu = ReplyKeyboardMarkup([
    ["🇬🇧 English", "🇧🇩 বাংলা"],
    ["❌ Cancel"]
], resize_keyboard=True)

cancel_menu = ReplyKeyboardMarkup([
    ["❌ Cancel"]
], resize_keyboard=True)

admin_menu = ReplyKeyboardMarkup([
    ["👥 All Users", "📋 All Tasks"],
    ["💳 Pending Withdrawals", "📊 Stats"],
    ["❌ Cancel"]
], resize_keyboard=True)

# ==================== HELPERS ====================

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

# ==================== START ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user:
        create_user(user.id, user.username or "NoUsername", user.first_name or "User")
        db_user = get_user(user.id)
    
    if db_user[10] == 1:
        await update.message.reply_text("👋 Welcome Admin!", reply_markup=admin_menu)
    else:
        await update.message.reply_text("👋 Welcome!\nUse the buttons below:", reply_markup=main_menu)

# ==================== MESSAGE HANDLER ====================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    db_user = get_user(user_id)
    
    if not db_user:
        await start(update, context)
        return
    
    is_admin = db_user[10] == 1
    
    # CANCEL
    if text == "❌ Cancel":
        user_states.pop(user_id, None)
        withdraw_states.pop(user_id, None)
        if is_admin:
            await update.message.reply_text("❌ Cancelled!", reply_markup=admin_menu)
        else:
            await update.message.reply_text("❌ Cancelled!", reply_markup=main_menu)
        return
    
    # ADMIN
    if is_admin:
        if text == "👥 All Users":
            users = get_all_users()
            msg = "👥 All Users:\n\n"
            for u in users[:30]:
                msg += f"🆔 {u[1]} | @{u[2] or 'N/A'} | Balance: {u[3]:.2f} BDT\n"
            await update.message.reply_text(msg, reply_markup=admin_menu)
            return
        
        if text == "📋 All Tasks":
            tasks = get_all_tasks()
            if tasks:
                msg = "📋 All Tasks:\n\n"
                for t in tasks[:20]:
                    msg += f"ID: {t[0]} | User: @{t[9]} | Status: {t[6]} | Reward: {t[7]:.2f} BDT\n"
                await update.message.reply_text(msg, reply_markup=admin_menu)
            else:
                await update.message.reply_text("No tasks found.", reply_markup=admin_menu)
            return
        
        if text == "💳 Pending Withdrawals":
            pending = get_pending_withdrawals()
            if pending:
                msg = "💳 Pending Withdrawals:\n\n"
                for w in pending:
                    msg += f"ID: {w[0]} | @{w[8]} | {w[2]:.2f} BDT | {w[3]}\n"
                await update.message.reply_text(msg, reply_markup=admin_menu)
            else:
                await update.message.reply_text("No pending withdrawals.", reply_markup=admin_menu)
            return
        
        if text == "📊 Stats":
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(balance) FROM users")
            total_balance = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'")
            pending_withdraw = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM instagram_tasks WHERE status = 'pending'")
            pending_tasks = cursor.fetchone()[0]
            await update.message.reply_text(
                f"📊 Stats:\n\n👥 Users: {total_users}\n💰 Balance: {total_balance:.2f} BDT\n⏳ Pending Tasks: {pending_tasks}\n⏳ Pending Withdrawals: {pending_withdraw}",
                reply_markup=admin_menu
            )
            return
    
    # MAIN MENU
    if text == "📋 Task":
        await update.message.reply_text("📋 Select Task:", reply_markup=task_menu)
        return
    
    if text == "💰 Balance":
        await update.message.reply_text(
            f"💰 Your Balance\n\nTotal: {db_user[3]:.2f} BDT\nEarned: {db_user[4]:.2f} BDT",
            reply_markup=main_menu
        )
        return
    
    if text == "💳 Withdraw":
        if db_user[3] < 50:
            await update.message.reply_text(f"❌ Min 50 BDT.\nYour Balance: {db_user[3]:.2f} BDT", reply_markup=main_menu)
            return
        await update.message.reply_text("💳 Select method:", reply_markup=withdraw_menu)
        return
    
    if text == "👤 Profile":
        await update.message.reply_text(
            f"👤 Your Profile\n\nID: {user_id}\nUsername: @{db_user[1] or 'N/A'}\nBalance: {db_user[3]:.2f} BDT",
            reply_markup=main_menu
        )
        return
    
    if text == "🔗 Refer":
        await update.message.reply_text(
            f"🔗 Referral Program\n\nEarn 10% commission!\n\nYour link:\nhttps://t.me/easyearnultimate_bot?start=ref_{db_user[6]}\n\nCommission: {db_user[8]:.2f} BDT",
            reply_markup=main_menu
        )
        return
    
    if text == "🌐 Language":
        await update.message.reply_text("🌐 Select Language:", reply_markup=language_menu)
        return
    
    # TASK
    if text == "📱 Insta 2FA 4 BDT":
        user_states[user_id] = {'task': 'instagram'}
        await update.message.reply_text(
            "⏳ 24h review\n📱 Create Inst (2FA)\n💰 Reward: 4 BDT",
            reply_markup=insta_menu
        )
        return
    
    if text == "📘 Facebook":
        await update.message.reply_text("📘 Coming soon!", reply_markup=task_menu)
        return
    
    # INSTAGRAM
    if text == "✅ Start" and user_id in user_states and user_states[user_id].get('task') == 'instagram':
        username, password = generate_credentials()
        task_id = create_instagram_task(db_user[0], username, password)
        user_states[user_id]['task_id'] = task_id
        user_states[user_id]['step'] = 'credentials'
        await update.message.reply_text(
            f"✅ Created!\n\nUsername: {username}\nPassword: {password}\n\nPlease login.",
            reply_markup=insta_actions
        )
        return
    
    if text == "🎥 Video" and user_id in user_states and user_states[user_id].get('task') == 'instagram':
        await update.message.reply_text("🎥 Video link here", reply_markup=insta_menu)
        return
    
    if text == "🔐 Set 2FA":
        if user_id in user_states and user_states[user_id].get('step') == 'credentials':
            user_states[user_id]['step'] = 'waiting'
            await update.message.reply_text("📱 Enter 2FA Secret Key:", reply_markup=cancel_menu)
        else:
            await update.message.reply_text("No active task", reply_markup=main_menu)
        return
    
    if user_id in user_states and user_states[user_id].get('step') == 'waiting':
        key = text.strip().upper()
        code = generate_authenticator_code(key)
        if code:
            task_id = user_states[user_id]['task_id']
            update_instagram_task(task_id, 'pending', key, code)
            user_states[user_id]['step'] = 'done'
            await update.message.reply_text(f"✅ Code: {code}\nClick Done:", reply_markup=done_menu)
        else:
            await update.message.reply_text("Invalid Key!", reply_markup=cancel_menu)
        return
    
    if text == "✅ Done":
        if user_id in user_states and user_states[user_id].get('step') == 'done':
            task_id = user_states[user_id]['task_id']
            update_instagram_task(task_id, 'completed')
            add_balance(db_user[0], 4.00)
            user_states.pop(user_id, None)
            await update.message.reply_text("✅ Done! +4 BDT", reply_markup=main_menu)
        else:
            await update.message.reply_text("No active task", reply_markup=main_menu)
        return
    
    # WITHDRAW
    if text == "📱 Bkash":
        withdraw_states[user_id] = {'method': 'Bkash', 'step': 'number'}
        await update.message.reply_text("Enter Bkash number:", reply_markup=cancel_menu)
        return
    
    if text == "📱 Nagad":
        withdraw_states[user_id] = {'method': 'Nagad', 'step': 'number'}
        await update.message.reply_text("Enter Nagad number:", reply_markup=cancel_menu)
        return
    
    if user_id in withdraw_states and withdraw_states[user_id].get('step') == 'number':
        if text.isdigit() and len(text) == 11:
            withdraw_states[user_id]['number'] = text
            withdraw_states[user_id]['step'] = 'amount'
            await update.message.reply_text(f"Amount? Min 50 BDT. Balance: {db_user[3]:.2f}", reply_markup=cancel_menu)
        else:
            await update.message.reply_text("Invalid number!", reply_markup=cancel_menu)
        return
    
    if user_id in withdraw_states and withdraw_states[user_id].get('step') == 'amount':
        try:
            amount = float(text)
            if amount < 50 or amount > db_user[3]:
                await update.message.reply_text(f"Invalid! Min 50, Max {db_user[3]:.2f}", reply_markup=cancel_menu)
                return
            method = withdraw_states[user_id]['method']
            number = withdraw_states[user_id]['number']
            create_withdrawal(db_user[0], amount, method, number)
            deduct_balance(db_user[0], amount)
            withdraw_states.pop(user_id, None)
            await update.message.reply_text(f"✅ Requested {amount:.2f} BDT", reply_markup=main_menu)
        except:
            await update.message.reply_text("Invalid amount!", reply_markup=cancel_menu)
        return
    
    # LANGUAGE
    if text == "🇬🇧 English":
        cursor.execute("UPDATE users SET language = 'en' WHERE telegram_id = ?", (user_id,))
        db.commit()
        await update.message.reply_text("✅ English", reply_markup=main_menu)
        return
    
    if text == "🇧🇩 বাংলা":
        cursor.execute("UPDATE users SET language = 'bn' WHERE telegram_id = ?", (user_id,))
        db.commit()
        await update.message.reply_text("✅ বাংলা", reply_markup=main_menu)
        return
    
    await update.message.reply_text("❌ Unknown", reply_markup=main_menu)

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
