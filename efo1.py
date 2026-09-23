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
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

# የሰጡትን ቦት ቶክን ይጠቀማል
TOKEN = "8996781987:AAHLXnjx_3ePT5MoJH_iBFCWSDPl2ZNfvc4"
bot = telebot.TeleBot(TOKEN)

# ፖስቱ የሚለቀቅበት ቻናል ዩዘርናም
DESTINATION_CHANNEL = "@ethiogamesmart"

# የሰጡት አዲስ የ Render Deployed URL
APP_URL = "https://efo1.onrender.com"

# የቦቱ ባለቤት (Owner) Telegram ID (አድሚን የመጨመር መብት ያለው)
OWNER_ID = 7396414604

# የተፈቀዱ Admin-ዎች ዝርዝር (አዲሶቹን አድሚኖች ጨምሮ)
ADMIN_IDS = [
    7396414604,  # Owner
    8055415178,  # Admin 1
    8169832183   # Admin 2
]

# ጊዜያዊ መረጃዎችን ለመያዝ (State management)
user_states = {}

# 1. ለነፃ ሆስቲንግ ሰርቨሮች (Deployment) የሚሆን የ Flask ዌብ ሰርቨር
app = Flask('')

@app.route('/')
def home():
    return "Smart Games Admin Bot is Active and Running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()


# /start ትዕዛዝ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ይህ ቦት የሚሰራው ለ Smart Games Admin-ዎች ብቻ ነው።")
        return
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 አዲስ ፖስት ፍጠር (Create Post)", callback_data="create_post"))
    
    # 🟢 Active Bot ቁልፍ የሰጡትን ሊንክ (APP_URL) በ Web App / URL መልክ ይከፍታል (ለሁሉም አድሚኖች)
    markup.add(InlineKeyboardButton("🟢 Active Bot (Wake Up)", url=APP_URL))
    
    # አድሚን የመጨመር እና የማሳየት መብት ያለው ባለቤቱ (OWNER_ID) ብቻ ነው
    if user_id == OWNER_ID:
        markup.add(InlineKeyboardButton("➕ Admin ጨምር", callback_data="add_admin"))
        markup.add(InlineKeyboardButton("📋 Admin ዎችን አሳይ", callback_data="list_admins"))

    bot.send_message(message.chat.id, "እንኳን ደህና መጡ ወደ Smart Games Admin Bot! የሚፈልጉትን ይምረጡ፦", reply_markup=markup)


# አድሚን ለመጨመር እና ፖስት ለመጀመር የሚረዱ Button ግብረ-መልሶች
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "ፈቃድ የለዎትም!", show_alert=True)
        return

    if call.data == "create_post":
        user_states[user_id] = {"step": "waiting_caption"}
        bot.send_message(user_id, "እባክዎ ለፖስቱ የሚሆነውን **ጽሑፍ (Caption)** ይላኩ:")
        bot.answer_callback_query(call.id)

    elif call.data == "add_admin":
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "ይህንን ማድረግ የሚችለው የቦቱ ባለቤት ብቻ ነው!", show_alert=True)
            return
        user_states[user_id] = {"step": "waiting_new_admin"}
        bot.send_message(user_id, "ሊያስገቡት የሚፈልጉትን የአድሚን **Telegram ID** ቁጥር ብቻ ይላኩ:")
        bot.answer_callback_query(call.id)

    elif call.data == "list_admins":
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "ፈቃድ የለዎትም!", show_alert=True)
            return
        admins_list = "\n".join([str(aid) for aid in ADMIN_IDS])
        bot.send_message(user_id, f"የተመዘገቡ Admin IDs:\n{admins_list}")
        bot.answer_callback_query(call.id)

    elif call.data == "confirm_post":
        state = user_states.get(user_id)
        if not state:
            return
        
        caption = state.get("caption")
        photo = state.get("photo")
        btn_text = state.get("btn_text")
        btn_url = state.get("btn_url")

        markup = InlineKeyboardMarkup()
        if btn_text and btn_url:
            markup.add(InlineKeyboardButton(btn_text, url=btn_url))

        try:
            if photo:
                bot.send_photo(DESTINATION_CHANNEL, photo, caption=caption, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(DESTINATION_CHANNEL, caption, parse_mode="Markdown", reply_markup=markup)
            
            bot.send_message(user_id, f"✅ ፖስቱ በተሳካ ሁኔታ ወደ {DESTINATION_CHANNEL} ተለጥፏል!")
        except Exception as e:
            bot.send_message(user_id, f"❌ መለጠፍ አልተቻለም: {str(e)}")
        
        user_states.pop(user_id, None)
        bot.answer_callback_query(call.id)

    elif call.data == "cancel_post":
        user_states.pop(user_id, None)
        bot.send_message(user_id, "❌ ፖስት ማዘጋጀቱ ተሰርዟል።")
        bot.answer_callback_query(call.id)


# የግብዓት መቀበያ ዋናው ክፍል
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document', 'video'])
def handle_steps(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return

    state = user_states.get(user_id)
    if not state:
        return

    step = state.get("step")

    if step == "waiting_new_admin":
        if user_id != OWNER_ID:
            user_states.pop(user_id, None)
            return
        try:
            new_admin_id = int(message.text.strip())
            if new_admin_id not in ADMIN_IDS:
                ADMIN_IDS.append(new_admin_id)
                bot.send_message(user_id, f"✅ አዲስ አድሚን (ID: {new_admin_id}) በተሳካ ሁኔታ ተጨመረ!")
            else:
                bot.send_message(user_id, "⚠️ ይህ አድሚን ቀደም ሲል ተመዝግቧል።")
        except ValueError:
            bot.send_message(user_id, "❌ ትክክለኛ የቁጥር Telegram ID ይላኩ።")
        user_states.pop(user_id, None)
        return

    if step == "waiting_caption":
        if not message.text:
            bot.send_message(user_id, "እባክዎ ትክክለኛ ጽሁፍ (Caption) ይላኩ:")
            return
        state["caption"] = message.text
        state["step"] = "waiting_photo"
        bot.send_message(user_id, "አሁን ደግሞ የፖስቱን **ፎቶ (Image)** ይላኩ። (ፎቶ ከሌለ 'skip' ብለው ይጻፉ):")

    elif step == "waiting_photo":
        if message.text and message.text.lower() == 'skip':
            state["photo"] = None
        elif message.photo:
            state["photo"] = message.photo[-1].file_id
        else:
            bot.send_message(user_id, "እባክዎ ትክክለኛ ፎቶ ይላኩ ወይም 'skip' ይበሉ።")
            return
        
        state["step"] = "waiting_button_name"
        bot.send_message(user_id, "ቀጥሎ ለፖስቱ የሚኖረው **Inline Button ስም (Button Name)** ይላኩ፦\n(ቁልፍ ካልፈለጉ 'skip' ይበሉ)")

    elif step == "waiting_button_name":
        if not message.text:
            bot.send_message(user_id, "እባክዎ የቁልፍ ስም በጽሁፍ ይላኩ:")
            return
        
        text = message.text.strip()
        if text.lower() == 'skip':
            state["btn_text"] = None
            state["btn_url"] = None
            show_preview(bot, user_id, state)
        else:
            state["btn_text"] = text
            state["step"] = "waiting_button_url"
            bot.send_message(user_id, f"አሁን ደግሞ ለቁልፉ የሚሆነውን **ሊንክ (URL Link)** ይላኩ\n(ምሳሌ: `https://t.me/...`):")

    elif step == "waiting_button_url":
        if not message.text:
            bot.send_message(user_id, "እባክዎ ትክክለኛ ሊንክ ይላኩ:")
            return
        
        url = message.text.strip()
        state["btn_url"] = url
        show_preview(bot, user_id, state)

def show_preview(bot, user_id, state):
    bot.send_message(user_id, "📋 **የተዘጋጀው ፖስት Preview ይህን ይመስላል:**")
    
    markup = InlineKeyboardMarkup()
    if state.get("btn_text") and state.get("btn_url"):
        markup.add(InlineKeyboardButton(state["btn_text"], url=state["btn_url"]))

    confirm_markup = InlineKeyboardMarkup()
    confirm_markup.add(
        InlineKeyboardButton("✅ ፖስት አድርግ (Post)", callback_data="confirm_post"),
        InlineKeyboardButton("❌ ሰርዝ (Cancel)", callback_data="cancel_post")
    )

    try:
        if state.get("photo"):
            bot.send_photo(user_id, state["photo"], caption=state.get("caption"), parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(user_id, state.get("caption"), parse_mode="Markdown", reply_markup=markup)
        
        bot.send_message(user_id, "ይህን ፖስት ወደ ቻናሉ ለመልቀቅ ከታች ያለውን ይጫኑ:", reply_markup=confirm_markup)
    except Exception as e:
        bot.send_message(user_id, f"ስህተት ተፈጥሯል: {str(e)}")
        user_states.pop(user_id, None)

# ዋናውን ሰርቨር እና ቦቱን በአንድ ላይ ማስጀመር
if __name__ == '__main__':
    print("የዌብ ሰርቨር (Flask) እየተጀመረ ነው...")
    keep_alive()
    print("Smart Games Admin Bot በንቃት (Polling) እየሰራ ነው...")
    bot.infinity_polling()
