import os
import threading
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running!"


def run_web():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# Web server በ background እንዲሰራ ማድረግ
threading.Thread(target=run_web, daemon=True).start()

# ከዚህ በታች የእርስዎ የቦት ኮድ ይ ቀጥላል...

import logging
import json
import os
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# የሎግ ማስተካከያ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# የቦቱ ቶክን፣ ዩዘርኔም እና የአድሚን ID
TOKEN = "8699981749:AAHVNnQFzwY2RsTJHGcQe1hQlsIBYSwWWH4"
BOT_USERNAME = "@betesebbingo2_bot"
ADMIN_ID = 1124325056

# የቻናል ሊንክ እና የቻናል ID (በቁጥር የሚጀምር ID ከሆኑ int በመጠቀም መፈተሽ አለበት)
CHANNEL_URL = "https://t.me/All_Best_Games_Zone"
CHANNEL_ID = -1002274889155 

# ዳታዎችን በፋይል ለማስቀመጥ የሚረዱ የፋይል ስሞች
DB_FILE = "bot_database.json"

def load_data():
    """ከፋይል ዳታዎችን ማንበብ (Termux ሲዘጋ እንዳይጠፉ)"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                balances = {int(k): v for k, v in data.get("balances", {}).items()}
                referrals = {int(k): v for k, v in data.get("referrals", {}).items()}
                users = set(int(uid) for uid in data.get("users", []))
                return balances, referrals, users
        except Exception as e:
            print(f"ዳታዎችን ሲያነብ ስህተት ተፈጥሯል: {e}")
    return {}, {}, set()

def save_data():
    """ዳታዎችን በቋሚነት ፋይል ላይ መጻፍ"""
    data = {
        "balances": user_balances,
        "referrals": user_referrals,
        "users": list(all_users)
    }
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"ዳታዎችን ሲያስቀምጥ ስህተት ተፈጥሯል: {e}")

# ዳታዎችን መጫን
user_balances, user_referrals, all_users = load_data()

# 1. /start ሲሉ የሚሰጠው ምላሽ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_first_name = user.first_name
    
    all_users.add(user_id)

    if user_id not in user_balances:
        user_balances[user_id] = 50.0
        user_referrals[user_id] = 0
    
    save_data()

    # ሪፈራል ኮድ ማረጋገጥ
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            inviter_id = int(args[0].split("_")[1])
            if inviter_id != user_id:
                if inviter_id in user_balances:
                    user_balances[inviter_id] += 10.0
                    user_referrals[inviter_id] += 1
                    save_data()
                    try:
                        await context.bot.send_message(
                            chat_id=inviter_id,
                            text=f"🎉 እንኳን ደስ አለዎት! አዲስ ሰው ጋብዘዋል፤ 10.00 ብር ወደ አካውንትዎ ተጨምሯል! 💰"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass

    # ቻናል መቀላቀሉን በ ID ማረጋገጥ
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["left", "kicked"]:
            await ask_to_join(update, user_first_name)
            return
    except Exception:
        await ask_to_join(update, user_first_name)
        return

    await show_main_menu(update.message, user_first_name, user_id)

# 2. /menu ሲሉ ዋናውን ሜኑ የሚያመጣ ትዕዛዝ
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_first_name = user.first_name
    
    all_users.add(user_id)

    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["left", "kicked"]:
            await ask_to_join(update, user_first_name)
            return
    except Exception:
        await ask_to_join(update, user_first_name)
        return

    await show_main_menu(update.message, user_first_name, user_id)

async def ask_to_join(update: Update, user_first_name: str):
    join_keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Complete Join (ቼክ አድርግ)", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(join_keyboard)

    text = (
        f"👋 ሰላም {user_first_name}!\n\n"
        f"ቦቱን ለመጠቀም መጀመሪያ ከታች ያለውን ቻናል መቀላቀል (Join ማድረግ) አለብዎት።\n"
        f"ቻናሉን ከተቀላቀሉ በኋላ **'Complete Join'** የሚለውን ይጫኑ!"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# Complete Join አዝራር ሲጫን
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data == "check_join":
        user_id = query.from_user.id
        user_first_name = query.from_user.first_name

        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status in ["left", "kicked"]:
                await query.answer("⚠️ እባክዎ መጀመሪያ ቻናሉን Join ያድርጉ!", show_alert=True)
                return
        except Exception:
            await query.answer("⚠️ እባክዎ መጀመሪያ ቻናሉን Join ያድርጉ!", show_alert=True)
            return

        # ቻናሉን ገብቷል -> ወደ ቀጣዩ ደረጃ (ሜኑ) እናልፋለን
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        
        await show_main_menu(query.message, user_first_name, user_id)

async def show_main_menu(message, user_first_name: str, user_id: int):
    if user_id == ADMIN_ID:
        admin_notif = (
            "👑 አድሚን ሆኖ ገብቷል!\n"
            "- ተጠቃሚ ለማየት: `/checklist <user_id>`\n"
            "- ጠቅላላ ተጠቃሚዎችን ለማየት: `checkall`\n"
            "- መልዕክት ለማሰራጨት: `/broadcast <መልዕክት>`"
        )
        await message.reply_text(admin_notif)

    keyboard = [
        [KeyboardButton("🎮 Play Bole Bingo")],
        [KeyboardButton("📝 Register"), KeyboardButton("🌐 Check Balance")],
        [KeyboardButton("💳 Deposit"), KeyboardButton("💰 Withdraw")],
        [KeyboardButton("🔗 Invite & Earn"), KeyboardButton("📞 Contact Support")],
        [KeyboardButton("📖 Instruction"), KeyboardButton("🎁 Transfer")],
        [KeyboardButton("📱 Share Contact (ስልክ ቁጥር አጋራ)", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    inline_keyboard = [
        [InlineKeyboardButton("🎮 Play Beteseb Bingo", web_app=WebAppInfo(url="https://grandbingo.free.nf"))]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    welcome_message = (
        f"✅ ቻናሉን በተሳካ ሁኔታ ተቀላቀለዋል!\n"
        f"👋 Welcome {user_first_name} to Beteseb Bingo! Choose an Option below.\n\n"
        "🔗 ሰዎችን በመጋበዝ በሰው ቁጥር 10 ብር ይሸለሙ!\n"
        "🎮 ጨዋታውን በቀጥታ ቦቱ ውስጥ ለመክፈት ከታች ያለውን ቁልፍ ይጫኑ:"
    )
    
    await message.reply_text(welcome_message, reply_markup=reply_markup)
    await message.reply_text("👇 ጨዋታውን ለመጀመር እዚህ ይጫኑ:", reply_markup=inline_markup)

# የአድሚን ትዕዛዞች
async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ ይቅርታ, ይህንን ትዕዛዝ መጠቀም የሚችሉት አድሚኖች ብቻ ናቸው።")
        return

    if not context.args:
        await update.message.reply_text("⚠️ አጠቃቀም: `/check <user_id>`", parse_mode="Markdown")
        return

    try:
        target_id = int(context.args[0])
        balance = user_balances.get(target_id, "የለም / አልተመዘገበም")
        referrals = user_referrals.get(target_id, 0)
        
        await update.message.reply_text(
            f"🔍 **የተጠቃሚ መረጃ:**\n🆔 ID: `{target_id}`\n💰 ቀሪ ሂሳብ: `{balance}` ብር\n👥 ሪፈራል: `{referrals}` ሰው",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("⚠️ ትክክለኛ የሰው ID ያስገቡ።")

async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ ይቅርታ, ይህንን ትዕዛዝ መጠቀም የሚችሉት አድሚኖች ብቻ ናቸው።")
        return

    total_users = len(all_users)
    stats_text = f"📊 **የቦቱ ተጠቃሚዎች ስታትስቲክስ:**\n\n👥 ጠቅላላ ተጠቃሚዎች ብዛት: `{total_users}`\n\n"
    stats_text += "📜 **የተጠቃሚዎች መታወቂያ (IDs) ዝርዝር:**\n"

    for uid in list(all_users)[:30]:
        bal = user_balances.get(uid, 0)
        ref = user_referrals.get(uid, 0)
        stats_text += f"• ` {uid} ` (💰 {bal}ብር, 👥 {ref}ሪፈራል)\n"

    if total_users > 30:
        stats_text += f"\n...እና ሌሎችም {total_users - 30} ተጠቃሚዎች አሉ።"

    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ ይቅርታ, አድሚን ብቻ ናቸው የሚጠቀሙት።")
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("⚠️ አጠቃቀም: `/broadcast <መልዕክት>`", parse_mode="Markdown")
        return

    success_count = 0
    fail_count = 0
    status_msg = await update.message.reply_text("⏳ መልዕክቱ ለሁሉም ተጠቃሚዎች በመላክ ላይ ነው...")

    for uid in all_users:
        try:
            await context.bot.send_message(chat_id=uid, text=message_text, parse_mode="Markdown")
            success_count += 1
        except Exception:
            fail_count += 1

    await status_msg.edit_text(f"✅ ብሮድካስት ተጠናቋል!\n📤 የደረሳቸው: {success_count}\n❌ ያልደረሳቸው: {fail_count}")

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone_number = contact.phone_number
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"መረጃዎ ደርሶናል! {user_name}፣ ስልክ ቁጥርዎ ({phone_number}) ተመዝግቧል።")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_first_name = user.first_name
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["left", "kicked"]:
            await ask_to_join(update, user_first_name)
            return
    except Exception:
        await ask_to_join(update, user_first_name)
        return

    text = update.message.text
    
    all_users.add(user_id)
    if user_id not in user_balances:
        user_balances[user_id] = 30.0
        user_referrals[user_id] = 0
    
    save_data()

    if text == "🎮 Play Beteseb Bingo ":
        await update.message.reply_text("👇 እባክዎ ከላይ የተላከውን የጨዋታ አዝራር ይጠቀሙ።")
    elif text == "📝 Register":
        await update.message.reply_text("📝 ለመመዝገብ እባክዎ ስልክ ቁጥርዎን ከታች ባለው አዝራር ያጋሩ።")
    elif text == "🌐 Check Balance":
        balance = user_balances[user_id]
        referrals = user_referrals[user_id]
        await update.message.reply_text(f"💰 ቀሪ ሂሳብ: **{balance:.2f} ብር**\n👥 የጋበዟቸው: **{referrals} ሰው**")
    elif text == "🔗 Invite & Earn":
        referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        await update.message.reply_text(f"🔗 **ሊንክዎ:**\n`{referral_link}`\n\nእያንዳንዱ ሰው ሲመጣ 10 ብር ያግኙ!")
    elif text == "💳 Deposit":
        await update.message.reply_text("💳 ገንዘብ ለማስገባት መመሪያዎችን ይከተሉ።")
    elif text == "💰 Withdraw":
        await update.message.reply_text("💰 ገንዘብ ለማውጣት አነስተኛውን ሂሳብ ያሟሉ።")
    elif text == "📞 Contact Support":
        await update.message.reply_text("☎️ ድጋፍ ማዕከልን ያግኙ።")
    elif text == "📖 Instruction":
        await update.message.reply_text("📖 የጨዋታ መመሪያዎች...")
    elif text == "🎁 Transfer":
        await update.message.reply_text("🎁 ሂሳብ ለማስተላለፍ የጓደኛ Phone ያስገቡ።")
    else:
        await update.message.reply_text("እባክዎ ከታች ያሉትን አማራጮች ይጠቀሙ።")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("checklist", check_user))
    application.add_handler(CommandHandler("checkall", bot_stats))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("EFO Bingo በቻናል ID እና ትክክለኛ ቼክ በመሥራት ላይ ነው...")
    application.run_polling()

if __name__ == "__main__":
    main()
