import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import string
import time
from datetime import datetime

# Bot token from BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

# Admin IDs (Add admin Telegram IDs here)
ADMIN_IDS = [123456789, 987654321]  # Replace with actual admin IDs

# Data file to store user data
DATA_FILE = "user_data.json"

# Default language
DEFAULT_LANG = "bn"  # bn for Bengali, en for English

# Language translations
LANG = {
    "bn": {
        "main_menu": "🔰 স্বাগতম! অনুগ্রহ করে একটি অপশন নির্বাচন করুন:",
        "task": "📋 টাস্ক",
        "balance": "💰 ব্যালেন্স",
        "withdraw": "💸 উইথড্র",
        "profile": "👤 প্রোফাইল",
        "refer": "🔗 রেফার",
        "language": "🌐 ভাষা",
        "task_menu": "📋 একটি টাস্ক নির্বাচন করুন:",
        "instagram_2fa": "Instagram 2FA",
        "facebook": "Facebook",
        "cancel": "❌ বাতিল",
        "task_description": "⏳ রিভিউ সময়: 24 ঘন্টা\n\n📋 টাস্ক: 📱 Inst (2FA) তৈরি করুন\n\n📄 বিবরণ: এই টাস্কে, আপনাকে শুধুমাত্র একটি আসল মোবাইল ডিভাইস ব্যবহার করে একটি নতুন Inst অ্যাকাউন্ট তৈরি করতে হবে।\n🔐 প্রয়োজন!\nআপনাকে টেলিগ্রাম বট দ্বারা প্রদত্ত তথ্য ব্যবহার করতে হবে নিবন্ধনের জন্য।\n\n❗যদি আপনি আপনার নিজের তথ্য ব্যবহার করেন, আপনার আবেদন যাচাই ছাড়াই প্রত্যাখ্যান করা হবে।\n\nনিবন্ধনের পর:\n👉 কোন তথ্য পাঠানোর প্রয়োজন নেই\n✅ শুধু "অ্যাকাউন্ট নিবন্ধিত" বাটনে ক্লিক করুন\n\n✍️ রিপোর্ট নির্দেশনা:\n.\n\n⏳ রিভিউ সময়: 24 ঘন্টা",
        "start": "▶️ শুরু করুন",
        "video": "🎥 ভিডিও",
        "credentials": "🔑 আপনার অ্যাকাউন্টের তথ্য:\n\n👤 ইউজারনেম: {username}\n🔒 পাসওয়ার্ড: {password}\n\nঅনুগ্রহ করে এই তথ্য ব্যবহার করে অ্যাকাউন্ট তৈরি করুন।",
        "set_2fa": "🔐 2FA সেট করুন",
        "ask_2fa": "🔐 অনুগ্রহ করে আপনার 2FA কোডটি লিখুন (Authenticator অ্যাপ থেকে):",
        "2fa_code": "✅ আপনার 2FA কোড: {code}\n\nঅনুগ্রহ করে এই কোডটি ব্যবহার করুন এবং Done বাটনে ক্লিক করুন।",
        "done": "✅ সম্পন্ন",
        "main_menu_return": "🔰 মেইন মেনুতে ফিরে এসেছেন।",
        "balance_info": "💰 আপনার মোট ব্যালেন্স: {balance} টাকা",
        "withdraw_menu": "💸 উইথড্র মেনু\n💰 আপনার ব্যালেন্স: {balance} টাকা\n\nউইথড্র পদ্ধতি নির্বাচন করুন:",
        "bkash": "বিকাশ",
        "nagad": "নগদ",
        "enter_number": "📱 অনুগ্রহ করে আপনার {method} নম্বরটি লিখুন:",
        "enter_amount": "💰 আপনি কত টাকা তুলতে চান?\n\n⚠️ ন্যূনতম উইথড্র: ৫০ টাকা",
        "withdraw_success": "✅ আপনার উইথড্র অনুরোধ গৃহীত হয়েছে!\n📱 {method}: {number}\n💰 পরিমাণ: {amount} টাকা\n\nঅনুরোধটি প্রক্রিয়াকরণ করা হচ্ছে।",
        "withdraw_fail": "❌ উইথড্র ব্যর্থ হয়েছে। ন্যূনতম উইথড্র ৫০ টাকা।",
        "profile_info": "👤 আপনার প্রোফাইল:\n🆔 আইডি: {user_id}\n👤 ইউজারনেম: @{username}\n📅 জয়েন তারিখ: {join_date}\n💰 ব্যালেন্স: {balance} টাকা",
        "refer_info": "🔗 আপনার রেফার লিংক:\n{refer_link}\n\n🎁 সারাজীবন ১০% কমিশন!\n\nআপনার বন্ধুদের আমন্ত্রণ জানান এবং কমিশন উপার্জন করুন!",
        "language_menu": "🌐 ভাষা নির্বাচন করুন:",
        "lang_bn": "বাংলা",
        "lang_en": "English",
        "lang_changed": "✅ ভাষা পরিবর্তন করা হয়েছে: {lang}",
        "invalid_option": "❌ ভুল অপশন। অনুগ্রহ করে পুনরায় চেষ্টা করুন।",
        "enter_username": "👤 অনুগ্রহ করে আপনার ইউজারনেম লিখুন:",
        "enter_password": "🔒 অনুগ্রহ করে আপনার পাসওয়ার্ড লিখুন:",
        "task_started": "✅ টাস্ক শুরু হয়েছে!",
        "video_instruction": "🎥 ভিডিও নির্দেশনা দেখুন এবং অ্যাকাউন্ট তৈরি করুন।",
        "account_registered": "✅ অ্যাকাউন্ট নিবন্ধিত হয়েছে!",
        "admin_panel": "🔐 অ্যাডমিন প্যানেল",
        "admin_users": "👥 সব ইউজার",
        "admin_approve": "✅ টাস্ক এপ্রুভ করুন",
        "admin_back": "🔙 ফিরে যান",
        "admin_user_details": "👤 ইউজার ডিটেইলস:\n🆔 আইডি: {user_id}\n👤 ইউজারনেম: @{username}\n📅 জয়েন: {join_date}\n💰 ব্যালেন্স: {balance}\n📊 টাস্ক সম্পন্ন: {tasks_completed}\n✅ অনুমোদিত টাস্ক: {approved_tasks}",
        "admin_approve_task": "✅ টাস্ক এপ্রুভ করুন\nইউজার আইডি লিখুন:",
        "admin_task_approved": "✅ ইউজারের টাস্ক এপ্রুভ করা হয়েছে!",
        "admin_task_not_found": "❌ ইউজার বা টাস্ক পাওয়া যায়নি।"
    },
    "en": {
        "main_menu": "🔰 Welcome! Please select an option:",
        "task": "📋 Task",
        "balance": "💰 Balance",
        "withdraw": "💸 Withdraw",
        "profile": "👤 Profile",
        "refer": "🔗 Refer",
        "language": "🌐 Language",
        "task_menu": "📋 Select a task:",
        "instagram_2fa": "Instagram 2FA",
        "facebook": "Facebook",
        "cancel": "❌ Cancel",
        "task_description": "⏳ Review time: 24 h\n\n📋 Task: 📱 Create Inst (2FA)\n\n📄 Description: In this task, you must create a new Inst account using only a real mobile device.\n🔐 REQUIRED!\nYou must use the information provided by the Telegram bot to register.\n\n❗If you use your own information, your application will be REJECTED without verification.\n\nAfter registration:\n👉 No need to send any info\n✅ Just click the \"Account Registered\" button\n\n✍️ Report instruction:\n.\n\n⏳ Review time: 24 h",
        "start": "▶️ Start",
        "video": "🎥 Video",
        "credentials": "🔑 Your account credentials:\n\n👤 Username: {username}\n🔒 Password: {password}\n\nPlease use this information to create the account.",
        "set_2fa": "🔐 Set 2FA",
        "ask_2fa": "🔐 Please enter your 2FA code (from Authenticator app):",
        "2fa_code": "✅ Your 2FA code: {code}\n\nPlease use this code and click Done button.",
        "done": "✅ Done",
        "main_menu_return": "🔰 Returned to main menu.",
        "balance_info": "💰 Your total balance: {balance} Taka",
        "withdraw_menu": "💸 Withdraw Menu\n💰 Your balance: {balance} Taka\n\nSelect withdrawal method:",
        "bkash": "Bkash",
        "nagad": "Nagad",
        "enter_number": "📱 Please enter your {method} number:",
        "enter_amount": "💰 How much do you want to withdraw?\n\n⚠️ Minimum withdrawal: 50 Taka",
        "withdraw_success": "✅ Your withdrawal request has been accepted!\n📱 {method}: {number}\n💰 Amount: {amount} Taka\n\nYour request is being processed.",
        "withdraw_fail": "❌ Withdrawal failed. Minimum withdrawal is 50 Taka.",
        "profile_info": "👤 Your Profile:\n🆔 ID: {user_id}\n👤 Username: @{username}\n📅 Join Date: {join_date}\n💰 Balance: {balance} Taka",
        "refer_info": "🔗 Your Refer Link:\n{refer_link}\n\n🎁 Lifetime 10% Commission!\n\nInvite your friends and earn commission!",
        "language_menu": "🌐 Select Language:",
        "lang_bn": "বাংলা",
        "lang_en": "English",
        "lang_changed": "✅ Language changed to: {lang}",
        "invalid_option": "❌ Invalid option. Please try again.",
        "enter_username": "👤 Please enter your username:",
        "enter_password": "🔒 Please enter your password:",
        "task_started": "✅ Task started!",
        "video_instruction": "🎥 Watch video instruction and create account.",
        "account_registered": "✅ Account registered!",
        "admin_panel": "🔐 Admin Panel",
        "admin_users": "👥 All Users",
        "admin_approve": "✅ Approve Task",
        "admin_back": "🔙 Back",
        "admin_user_details": "👤 User Details:\n🆔 ID: {user_id}\n👤 Username: @{username}\n📅 Join: {join_date}\n💰 Balance: {balance}\n📊 Tasks Completed: {tasks_completed}\n✅ Approved Tasks: {approved_tasks}",
        "admin_approve_task": "✅ Approve Task\nEnter User ID:",
        "admin_task_approved": "✅ User's task approved!",
        "admin_task_not_found": "❌ User or task not found."
    }
}

# Load user data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Save user data
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Get user language
def get_lang(user_id):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str in data and 'lang' in data[user_id_str]:
        return data[user_id_str]['lang']
    return DEFAULT_LANG

# Get text in user's language
def get_text(user_id, key, **kwargs):
    lang_code = get_lang(user_id)
    text = LANG.get(lang_code, LANG[DEFAULT_LANG]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# Generate random username and password
def generate_credentials():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    return username, password

# Generate 2FA code
def generate_2fa():
    return ''.join(random.choices(string.digits, k=6))

# Generate refer link
def generate_refer_link(user_id):
    return f"https://t.me/your_bot_username?start=ref_{user_id}"

# Main menu keyboard
def main_menu_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "task"), callback_data="task"),
        InlineKeyboardButton(get_text(user_id, "balance"), callback_data="balance")
    )
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "withdraw"), callback_data="withdraw"),
        InlineKeyboardButton(get_text(user_id, "profile"), callback_data="profile")
    )
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "refer"), callback_data="refer"),
        InlineKeyboardButton(get_text(user_id, "language"), callback_data="language")
    )
    if str(user_id) in ADMIN_IDS:
        keyboard.add(InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    return keyboard

# Task menu keyboard
def task_menu_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "instagram_2fa"), callback_data="instagram_2fa"),
        InlineKeyboardButton(get_text(user_id, "facebook"), callback_data="facebook")
    )
    keyboard.add(InlineKeyboardButton(get_text(user_id, "cancel"), callback_data="cancel"))
    return keyboard

# Task action keyboard (Start, Video, Cancel)
def task_action_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "start"), callback_data="task_start"),
        InlineKeyboardButton(get_text(user_id, "video"), callback_data="task_video"),
        InlineKeyboardButton(get_text(user_id, "cancel"), callback_data="cancel")
    )
    return keyboard

# 2FA action keyboard
def twofa_action_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "set_2fa"), callback_data="set_2fa"),
        InlineKeyboardButton(get_text(user_id, "cancel"), callback_data="cancel")
    )
    return keyboard

# Done keyboard
def done_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(get_text(user_id, "done"), callback_data="done"))
    return keyboard

# Withdraw method keyboard
def withdraw_method_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "bkash"), callback_data="withdraw_bkash"),
        InlineKeyboardButton(get_text(user_id, "nagad"), callback_data="withdraw_nagad")
    )
    keyboard.add(InlineKeyboardButton(get_text(user_id, "cancel"), callback_data="cancel"))
    return keyboard

# Language keyboard
def language_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("বাংলা", callback_data="lang_bn"),
        InlineKeyboardButton("English", callback_data="lang_en")
    )
    keyboard.add(InlineKeyboardButton(get_text(user_id, "cancel"), callback_data="cancel"))
    return keyboard

# Admin panel keyboard
def admin_panel_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, "admin_users"), callback_data="admin_users"),
        InlineKeyboardButton(get_text(user_id, "admin_approve"), callback_data="admin_approve")
    )
    keyboard.add(InlineKeyboardButton(get_text(user_id, "admin_back"), callback_data="cancel"))
    return keyboard

# Admin users keyboard
def admin_users_keyboard(users_data, user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for uid, data in list(users_data.items())[:20]:  # Show first 20 users
        username = data.get('username', 'Unknown')
        keyboard.add(InlineKeyboardButton(f"@{username} ({uid})", callback_data=f"admin_user_{uid}"))
    keyboard.add(InlineKeyboardButton(get_text(user_id, "admin_back"), callback_data="admin_panel"))
    return keyboard

# Initialize user data
def init_user(user_id, username):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            "username": username,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "balance": 0,
            "tasks_completed": 0,
            "approved_tasks": 0,
            "lang": DEFAULT_LANG,
            "referrals": [],
            "current_task": None,
            "awaiting_withdraw": None,
            "awaiting_2fa": False,
            "generated_username": None,
            "generated_password": None
        }
        save_data(data)
    return data[user_id_str]

# /start command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    init_user(user_id, username)
    
    # Handle referral
    if message.text and 'ref_' in message.text:
        ref_id = message.text.split('ref_')[1]
        data = load_data()
        if ref_id in data and ref_id != str(user_id):
            data[ref_id]['referrals'].append(user_id)
            data[ref_id]['balance'] += 10  # Bonus for referral
            save_data(data)
            bot.send_message(ref_id, f"🎉 New referral! You earned 10 Taka bonus!")
    
    bot.send_message(
        user_id,
        get_text(user_id, "main_menu"),
        reply_markup=main_menu_keyboard(user_id)
    )

# Handle callback queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    username = call.from_user.username or "Unknown"
    user_data = init_user(user_id, username)
    data = load_data()
    
    # Cancel button - return to main menu
    if call.data == "cancel":
        bot.edit_message_text(
            get_text(user_id, "main_menu_return"),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Task menu
    if call.data == "task":
        bot.edit_message_text(
            get_text(user_id, "task_menu"),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=task_menu_keyboard(user_id)
        )
        return
    
    # Balance
    if call.data == "balance":
        balance = user_data.get('balance', 0)
        bot.edit_message_text(
            get_text(user_id, "balance_info", balance=balance),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Withdraw
    if call.data == "withdraw":
        balance = user_data.get('balance', 0)
        bot.edit_message_text(
            get_text(user_id, "withdraw_menu", balance=balance),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=withdraw_method_keyboard(user_id)
        )
        return
    
    # Profile
    if call.data == "profile":
        bot.edit_message_text(
            get_text(user_id, "profile_info", 
                    user_id=user_id,
                    username=username,
                    join_date=user_data.get('join_date', 'Unknown'),
                    balance=user_data.get('balance', 0)),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Refer
    if call.data == "refer":
        refer_link = generate_refer_link(user_id)
        bot.edit_message_text(
            get_text(user_id, "refer_info", refer_link=refer_link),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Language
    if call.data == "language":
        bot.edit_message_text(
            get_text(user_id, "language_menu"),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=language_keyboard(user_id)
        )
        return
    
    # Language change
    if call.data == "lang_bn" or call.data == "lang_en":
        lang_code = "bn" if call.data == "lang_bn" else "en"
        data[str(user_id)]['lang'] = lang_code
        save_data(data)
        lang_name = "বাংলা" if lang_code == "bn" else "English"
        bot.edit_message_text(
            get_text(user_id, "lang_changed", lang=lang_name),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Instagram 2FA task
    if call.data == "instagram_2fa":
        user_data['current_task'] = 'instagram_2fa'
        data[str(user_id)] = user_data
        save_data(data)
        
        bot.edit_message_text(
            get_text(user_id, "task_description"),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=task_action_keyboard(user_id)
        )
        return
    
    # Facebook task (not fully implemented)
    if call.data == "facebook":
        bot.answer_callback_query(call.id, "❌ Facebook task coming soon!")
        return
    
    # Task Start - Generate credentials
    if call.data == "task_start":
        username_gen, password_gen = generate_credentials()
        user_data['generated_username'] = username_gen
        user_data['generated_password'] = password_gen
        data[str(user_id)] = user_data
        save_data(data)
        
        bot.edit_message_text(
            get_text(user_id, "credentials", username=username_gen, password=password_gen),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=twofa_action_keyboard(user_id)
        )
        return
    
    # Task Video
    if call.data == "task_video":
        bot.answer_callback_query(call.id, "🎥 Video instruction will be sent here!")
        bot.send_message(
            user_id,
            get_text(user_id, "video_instruction"),
            reply_markup=task_action_keyboard(user_id)
        )
        return
    
    # Set 2FA
    if call.data == "set_2fa":
        user_data['awaiting_2fa'] = True
        data[str(user_id)] = user_data
        save_data(data)
        
        bot.edit_message_text(
            get_text(user_id, "ask_2fa"),
            chat_id=user_id,
            message_id=call.message.message_id
        )
        # Wait for user input
        bot.register_next_step_handler(call.message, process_2fa_input)
        return
    
    # Done - Task completed
    if call.data == "done":
        user_data['tasks_completed'] = user_data.get('tasks_completed', 0) + 1
        user_data['current_task'] = None
        user_data['generated_username'] = None
        user_data['generated_password'] = None
        user_data['awaiting_2fa'] = False
        data[str(user_id)] = user_data
        save_data(data)
        
        bot.edit_message_text(
            get_text(user_id, "account_registered"),
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Withdraw methods
    if call.data == "withdraw_bkash" or call.data == "withdraw_nagad":
        method = "Bkash" if call.data == "withdraw_bkash" else "Nagad"
        user_data['awaiting_withdraw'] = {'method': method, 'step': 'number'}
        data[str(user_id)] = user_data
        save_data(data)
        
        bot.edit_message_text(
            get_text(user_id, "enter_number", method=method),
            chat_id=user_id,
            message_id=call.message.message_id
        )
        bot.register_next_step_handler(call.message, process_withdraw_input)
        return
    
    # Admin Panel
    if call.data == "admin_panel":
        if str(user_id) not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ You are not an admin!")
            return
        
        bot.edit_message_text(
            "🔐 Admin Panel",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=admin_panel_keyboard(user_id)
        )
        return
    
    # Admin Users
    if call.data == "admin_users":
        if str(user_id) not in ADMIN_IDS:
            return
        
        users_data = load_data()
        bot.edit_message_text(
            "👥 All Users:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=admin_users_keyboard(users_data, user_id)
        )
        return
    
    # Admin User Details
    if call.data.startswith("admin_user_"):
        if str(user_id) not in ADMIN_IDS:
            return
        
        target_id = call.data.replace("admin_user_", "")
        users_data = load_data()
        if target_id in users_data:
            u_data = users_data[target_id]
            bot.edit_message_text(
                get_text(user_id, "admin_user_details",
                        user_id=target_id,
                        username=u_data.get('username', 'Unknown'),
                        join_date=u_data.get('join_date', 'Unknown'),
                        balance=u_data.get('balance', 0),
                        tasks_completed=u_data.get('tasks_completed', 0),
                        approved_tasks=u_data.get('approved_tasks', 0)),
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=admin_panel_keyboard(user_id)
            )
        return
    
    # Admin Approve Task
    if call.data == "admin_approve":
        if str(user_id) not in ADMIN_IDS:
            return
        
        bot.edit_message_text(
            get_text(user_id, "admin_approve_task"),
            chat_id=user_id,
            message_id=call.message.message_id
        )
        bot.register_next_step_handler(call.message, admin_approve_task_input)
        return

# Process 2FA input
def process_2fa_input(message):
    user_id = message.from_user.id
    user_data = load_data().get(str(user_id), {})
    
    if not user_data.get('awaiting_2fa', False):
        bot.send_message(user_id, "❌ No pending 2FA request.", reply_markup=main_menu_keyboard(user_id))
        return
    
    # Generate 2FA code
    code = generate_2fa()
    user_data['awaiting_2fa'] = False
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)
    
    bot.send_message(
        user_id,
        get_text(user_id, "2fa_code", code=code),
        reply_markup=done_keyboard(user_id)
    )

# Process withdraw input
def process_withdraw_input(message):
    user_id = message.from_user.id
    user_data = load_data().get(str(user_id), {})
    withdraw_info = user_data.get('awaiting_withdraw', {})
    
    if not withdraw_info:
        bot.send_message(user_id, "❌ No pending withdrawal.", reply_markup=main_menu_keyboard(user_id))
        return
    
    step = withdraw_info.get('step', '')
    
    if step == 'number':
        number = message.text.strip()
        # Validate number (basic check)
        if len(number) < 11:
            bot.send_message(user_id, "❌ Invalid number. Please enter a valid phone number.")
            bot.register_next_step_handler(message, process_withdraw_input)
            return
        
        withdraw_info['number'] = number
        withdraw_info['step'] = 'amount'
        user_data['awaiting_withdraw'] = withdraw_info
        data = load_data()
        data[str(user_id)] = user_data
        save_data(data)
        
        bot.send_message(user_id, get_text(user_id, "enter_amount"))
        bot.register_next_step_handler(message, process_withdraw_input)
        
    elif step == 'amount':
        try:
            amount = float(message.text.strip())
            balance = user_data.get('balance', 0)
            
            if amount < 50:
                bot.send_message(user_id, get_text(user_id, "withdraw_fail"))
                bot.send_message(user_id, get_text(user_id, "main_menu_return"), reply_markup=main_menu_keyboard(user_id))
                return
            
            if amount > balance:
                bot.send_message(user_id, f"❌ Insufficient balance! Your balance is {balance} Taka.")
                bot.register_next_step_handler(message, process_withdraw_input)
                return
            
            # Process withdrawal
            method = withdraw_info.get('method', 'Unknown')
            number = withdraw_info.get('number', 'Unknown')
            
            # Deduct balance
            user_data['balance'] = balance - amount
            user_data['awaiting_withdraw'] = None
            data = load_data()
            data[str(user_id)] = user_data
            save_data(data)
            
            bot.send_message(
                user_id,
                get_text(user_id, "withdraw_success", method=method, number=number, amount=amount),
                reply_markup=main_menu_keyboard(user_id)
            )
            
        except ValueError:
            bot.send_message(user_id, "❌ Please enter a valid number.")
            bot.register_next_step_handler(message, process_withdraw_input)

# Admin approve task input
def admin_approve_task_input(message):
    admin_id = message.from_user.id
    user_id = message.text.strip()
    
    data = load_data()
    if user_id not in data:
        bot.send_message(admin_id, get_text(admin_id, "admin_task_not_found"), reply_markup=main_menu_keyboard(admin_id))
        return
    
    # Approve task - add balance
    user_data = data[user_id]
    user_data['balance'] = user_data.get('balance', 0) + 50  # Add 50 Taka for task
    user_data['approved_tasks'] = user_data.get('approved_tasks', 0) + 1
    data[user_id] = user_data
    save_data(data)
    
    bot.send_message(admin_id, get_text(admin_id, "admin_task_approved"), reply_markup=admin_panel_keyboard(admin_id))
    bot.send_message(int(user_id), "✅ Your task has been approved! You earned 50 Taka!")

# Handle regular messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    # Check if user is in a process
    user_data = load_data().get(str(user_id), {})
    
    if user_data.get('awaiting_2fa', False):
        process_2fa_input(message)
    elif user_data.get('awaiting_withdraw', {}).get('step', '') in ['number', 'amount']:
        process_withdraw_input(message)
    else:
        bot.send_message(user_id, get_text(user_id, "invalid_option"), reply_markup=main_menu_keyboard(user_id))

# Start bot
print("Bot is running...")
bot.polling(none_stop=True)
