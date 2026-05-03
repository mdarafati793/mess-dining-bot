import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import time

# এখানে আপনার বটের আসল টোকেন দিন
TOKEN = "8581132689:AAF_x23qBXyzAjpckVTX602J80MSe8Pk0Oc"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# মেসের ডেটা সেভ রাখার জন্য ডিকশনারি
mess_data = {}

# --- Flask Server (Render এ অনলাইন রাখার জন্য) ---
@app.route('/')
def index():
    return "Bot is Live and Running!"

def run_server():
    app.run(host="0.0.0.0", port=8080)

# --- Bot Setup Flow ---
@bot.message_handler(commands=['start'])
def start_setup(message):
    mess_data.clear() # নতুন করে শুরু করলে আগের ডেটা ক্লিয়ার হবে
    mess_data['members'] = []
    
    msg = bot.reply_to(message, "👋 **মেস ডাইনিং ম্যানেজার বটে স্বাগতম!**\n\nচলুন মেস সেটআপ শুরু করি।\n\n🏢 **প্রথমে আপনার মেসের নাম লিখুন:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_mess_name)

def process_mess_name(message):
    mess_data['mess_name'] = message.text
    msg = bot.reply_to(message, "🍽 **প্রতিদিন কয় বেলা মিল চলবে?**\n(যেমন: 2 বা 3 লিখে সেন্ড করুন)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_meal_count)

def process_meal_count(message):
    mess_data['meal_count'] = message.text
    msg = bot.reply_to(message, "👤 **ডাইনিং ম্যানেজারের নাম কী?**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_manager_name)

def process_manager_name(message):
    mess_data['manager_name'] = message.text
    msg = bot.reply_to(message, "📅 **কত তারিখ ও কোন মাস থেকে মিল শুরু হবে?**\n(যেমন: ১ মে, ২০২৬)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_start_date)

def process_start_date(message):
    mess_data['start_date'] = message.text
    msg = bot.reply_to(message, "👥 **আপনার মেসে মোট কতজন মেম্বার খাবে?**\n(যেমন: 5)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_total_members)

def process_total_members(message):
    try:
        total = int(message.text)
        mess_data['total_members'] = total
        mess_data['current_member_index'] = 1
        
        msg = bot.reply_to(message, f"✅ ঠিক আছে! এবার একে একে {total} জনের নাম দিন।\n\n**(01) প্রথম জনের নাম লিখুন:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_member_name)
    except ValueError:
        msg = bot.reply_to(message, "⚠️ দয়া করে শুধু সংখ্যা লিখুন (যেমন: 5)। আবার মেম্বার সংখ্যা দিন:")
        bot.register_next_step_handler(msg, process_total_members)

def process_member_name(message):
    name = message.text
    mess_data['members'].append(name)
    current_index = mess_data['current_member_index']
    total = mess_data['total_members']
    
    bot.reply_to(message, f"({current_index:02d}). {name} ✅")
    
    if current_index < total:
        mess_data['current_member_index'] += 1
        next_index = mess_data['current_member_index']
        msg = bot.send_message(message.chat.id, f"**({next_index:02d}) পরবর্তী জনের নাম লিখুন:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_member_name)
    else:
        # সব নাম নেওয়া শেষ, ড্যাশবোর্ড দেখাবে
        show_dashboard(message)

# --- Dashboard Generate ---
def show_dashboard(message):
    bot.send_message(message.chat.id, "🎉 **Setup Complete! আপনার মেস সফলভাবে তৈরি হয়েছে।**", parse_mode="Markdown")
    
    dashboard_text = (
        f"🏢 **{mess_data.get('mess_name', 'মেসের নাম')}** 🏢\n"
        f"📅 **হিসাব শুরুর তারিখ:** {mess_data.get('start_date', 'তারিখ')}\n"
        f"👤 **ডাইনিং ম্যানেজার:** {mess_data.get('manager_name', 'ম্যানেজার')}\n\n"
        f"👥 **মোট মেম্বার:** {mess_data.get('total_members', 0)} জন\n"
        "👇 *নিচের বাটনগুলো থেকে আপনার অপশন বেছে নিন:*"
    )
    
    # ১০টি বাটন তৈরি
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🍽 মিল এন্ট্রি", callback_data="btn_meal_entry")
    btn2 = InlineKeyboardButton("💰 অ্যাড ব্যালেন্স", callback_data="btn_add_balance")
    btn3 = InlineKeyboardButton("🛒 বাজার খরচ ও বাকি", callback_data="btn_bazar")
    btn4 = InlineKeyboardButton("📈 চলতি মিল রেট", callback_data="btn_meal_rate")
    btn5 = InlineKeyboardButton("⚖️ মেম্বার ব্যালেন্স", callback_data="btn_member_balance")
    btn6 = InlineKeyboardButton("👩‍🍳 খালার বিল", callback_data="btn_khala_bill")
    btn7 = InlineKeyboardButton("✏️ হিসাব সংশোধন", callback_data="btn_edit_info")
    btn8 = InlineKeyboardButton("📝 মেস নোটস", callback_data="btn_notes")
    btn9 = InlineKeyboardButton("📜 হিস্টোরি/লগ", callback_data="btn_history")
    btn10 = InlineKeyboardButton("📄 মেস রিসিট", callback_data="btn_receipt")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)
    
    bot.send_message(message.chat.id, dashboard_text, reply_markup=markup, parse_mode="Markdown")

# --- Button Click Handler (Dashboard) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    # এই অংশে পরবর্তীতে প্রতিটি বাটনের কাজ (Input/Output) যোগ করা হবে
    bot.answer_callback_query(call.id, "ফিচারটি খুব শীঘ্রই আসছে!")
    bot.send_message(call.message.chat.id, f"আপনি **{call.data}** বাটনে ক্লিক করেছেন।")

# ড্যাশবোর্ড সরাসরি আনার কমান্ড
@bot.message_handler(commands=['dashboard', 'menu'])
def direct_dashboard(message):
    if 'mess_name' in mess_data:
        show_dashboard(message)
    else:
        bot.reply_to(message, "⚠️ আপনার মেস এখনো সেটআপ করা হয়নি। দয়া করে /start লিখে সেটআপ করুন।")

# --- Bot Polling ---
if __name__ == "__main__":
    # Flask সার্ভার আলাদা থ্রেডে চালানো হচ্ছে যেন Render ব্লক না হয়
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    
    print("Bot is running...")
    # বট কন্টিনিউয়াসলি মেসেজ রিসিভ করার জন্য
    bot.infinity_polling()
    
