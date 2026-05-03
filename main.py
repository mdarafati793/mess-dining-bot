import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import google.generativeai as genai

# --- API টোকেন ও কী সেটআপ ---
TOKEN = "8581132689:AAF_x23qBXyzAjpckVTX602J80MSe8Pk0Oc"
GEMINI_KEY = "AIzaSyDZIkwrK-B9EfcpgtMLKOX1eNY0S4ZRULM"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Gemini AI কনফিগারেশন
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- মেসের ডেটাবেস (In-Memory) ---
mess_data = {
    'mess_name': '',
    'meal_count': 0,
    'manager_name': '',
    'start_date': '',
    'total_members': 0,
    'members': [],      
    'balances': {},     
    'meals': {},        
    'bazar_cost': 0,    
    'bazar_list': [],   
    'bazar_baki': 0,    
    'notes': [],        
    'history': [],      
    'khala_bill': 0,    
    'khala_paid': []    
}

@app.route('/')
def index():
    return "AI-Powered Mess Bot is running perfectly!"

def run_server():
    app.run(host="0.0.0.0", port=8080)

# --- মেস সেটআপ শুরু ---
@bot.message_handler(commands=['start'])
def start_setup(message):
    global mess_data
    mess_data = {
        'mess_name': '', 'meal_count': 0, 'manager_name': '', 'start_date': '',
        'total_members': 0, 'members': [], 'balances': {}, 'meals': {},
        'bazar_cost': 0, 'bazar_list': [], 'bazar_baki': 0, 'notes': [],
        'history': [], 'khala_bill': 0, 'khala_paid': []
    }
    msg = bot.reply_to(message, "👋 **মেস ডাইনিং ম্যানেজার বটে স্বাগতম!**\n\n🏢 **প্রথমে আপনার মেসের নাম লিখুন:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_mess_name)

def process_mess_name(message):
    mess_data['mess_name'] = message.text
    msg = bot.reply_to(message, "🍽 **প্রতিদিন কয় বেলা মিল চলবে?**\n(যেমন: 2 বা 3 লিখে সেন্ড করুন)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_meal_count)

def process_meal_count(message):
    try:
        mess_data['meal_count'] = int(message.text)
        msg = bot.reply_to(message, "👤 **ডাইনিং ম্যানেজারের নাম কী?**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_manager_name)
    except:
        msg = bot.reply_to(message, "⚠️ শুধু সংখ্যা দিন। কয় বেলা মিল চলবে?")
        bot.register_next_step_handler(msg, process_meal_count)

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
        msg = bot.reply_to(message, f"✅ ঠিক আছে! এবার একে একে {total} জনের নাম দিন।\n\n**(01) প্রথম জনের নাম লিখুন:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_member_names, 1)
    except:
        msg = bot.reply_to(message, "⚠️ শুধু সংখ্যা দিন। মোট মেম্বার কতজন?")
        bot.register_next_step_handler(msg, process_total_members)

def process_member_names(message, index):
    name = message.text
    mess_data['members'].append(name)
    mess_data['balances'][name] = 0.0
    mess_data['meals'][name] = 0.0
    
    bot.reply_to(message, f"({index:02d}). {name} ✅")
    
    if index < mess_data['total_members']:
        msg = bot.send_message(message.chat.id, f"**({index+1:02d}) পরবর্তী জনের নাম লিখুন:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_member_names, index + 1)
    else:
        bot.send_message(message.chat.id, "🎉 **Setup Complete! আপনার মেস সফলভাবে তৈরি হয়েছে।**")
        show_dashboard(message)

# --- ড্যাশবোর্ড / হোম মেনু ---
def show_dashboard(message):
    dashboard_text = (
        f"🏢 **{mess_data['mess_name']}** 🏢\n"
        f"📅 **হিসাব শুরুর তারিখ:** {mess_data['start_date']}\n"
        f"👤 **ডাইনিং ম্যানেজার:** {mess_data['manager_name']}\n\n"
        f"👥 **মোট মেম্বার:** {mess_data['total_members']} জন\n"
        "👇 *নিচের বাটনগুলো থেকে আপনার অপশন বেছে নিন:*"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🍽 মিল এন্ট্রি", callback_data="btn_meal_entry"),
        InlineKeyboardButton("💰 অ্যাড ব্যালেন্স", callback_data="btn_add_balance"),
        InlineKeyboardButton("🛒 বাজার খরচ ও বাকি", callback_data="btn_bazar"),
        InlineKeyboardButton("📈 চলতি মিল রেট", callback_data="btn_meal_rate"),
        InlineKeyboardButton("⚖️ মেম্বার ব্যালেন্স", callback_data="btn_member_balance"),
        InlineKeyboardButton("👩‍🍳 খালার বিল", callback_data="btn_khala_bill"),
        InlineKeyboardButton("✏️ হিসাব সংশোধন", callback_data="btn_edit_info"),
        InlineKeyboardButton("📝 মেস নোটস", callback_data="btn_notes"),
        InlineKeyboardButton("📜 হিস্টোরি/লগ", callback_data="btn_history"),
        InlineKeyboardButton("📄 মেস রিসিট", callback_data="btn_receipt")
    )
    bot.send_message(message.chat.id, dashboard_text, reply_markup=markup, parse_mode="Markdown")

# --- বাটনের ক্লিক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # বোতামের লোডিং বন্ধ করার জন্য
    bot.answer_callback_query(call.id)

    # ড্যাশবোর্ডে ফিরে যাওয়া
    if call.data == "go_to_home":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        show_dashboard(call.message)
        return

    # ১. মিল এন্ট্রি
    if call.data == "btn_meal_entry":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        markup = InlineKeyboardMarkup(row_width=1)
        for name in mess_data['members']:
            markup.add(InlineKeyboardButton(name, callback_data=f"addmeal_{name}"))
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, "🍽 কার মিল যুক্ত করতে চান? নাম সিলেক্ট করুন:", reply_markup=markup)

    # ২. অ্যাড ব্যালেন্স
    elif call.data == "btn_add_balance":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        markup = InlineKeyboardMarkup(row_width=1)
        for name in mess_data['members']:
            markup.add(InlineKeyboardButton(name, callback_data=f"addbal_{name}"))
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, "💰 কার ব্যালেন্স অ্যাড করতে চান? নাম সিলেক্ট করুন:", reply_markup=markup)

    # ৩. বাজার খরচ ও বাকি
    elif call.data == "btn_bazar":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ বাজার খরচ যোগ", callback_data="bazar_add"),
            InlineKeyboardButton("🔴 বাজার বাকি যোগ", callback_data="bazar_baki_add"),
            InlineKeyboardButton("🟢 বাজার বাকি পরিশোধ", callback_data="bazar_pay"),
            InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home")
        )
        bot.send_message(chat_id, "🛒 বাজার ও বাকির হিসাব নির্বাচন করুন:", reply_markup=markup)

    # ৪. চলতি মিল রেট
    elif call.data == "btn_meal_rate":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        total_meals = sum(mess_data['meals'].values())
        rate = mess_data['bazar_cost'] / total_meals if total_meals > 0 else 0
        text = f"📈 **চলতি মিল রেট:**\n\n🛒 মোট বাজার খরচ: {mess_data['bazar_cost']} টাকা\n🍽 মোট মিল: {total_meals} টি\n\n💵 **বর্তমান মিল রেট: {rate:.2f} টাকা**"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    # ৫. মেম্বার ব্যালেন্স
    elif call.data == "btn_member_balance":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        total_meals = sum(mess_data['meals'].values())
        rate = mess_data['bazar_cost'] / total_meals if total_meals > 0 else 0
        text = "⚖️ **মেম্বারদের ব্যালেন্সের অবস্থা:**\n\n"
        for name in mess_data['members']:
            cost = mess_data['meals'][name] * rate
            bal = mess_data['balances'][name] - cost
            status = f"পাবে 🟢 {bal:.2f}" if bal >= 0 else f"দেবে 🔴 {abs(bal):.2f}"
            text += f"👤 {name}: মিল {mess_data['meals'][name]}টি | {status} টাকা\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    # ৬. খালার বিল
    elif call.data == "btn_khala_bill":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Add Bill", callback_data="khala_add"),
            InlineKeyboardButton("✅ Paid Bill", callback_data="khala_paid_list"),
            InlineKeyboardButton("❌ Unpaid Bill", callback_data="khala_unpaid_list"),
            InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home")
        )
        bot.send_message(chat_id, "👩‍🍳 খালার বিল অপশন:", reply_markup=markup)

    # ৭. হিসাব সংশোধন
    elif call.data == "btn_edit_info":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, "✏️ **সংশোধন:** যার তথ্য সংশোধন করবেন তার নাম এবং সঠিক মিল/টাকা কমা দিয়ে লিখে দিন।\n(যেমন: Arafat, 12)")
        bot.register_next_step_handler(msg, process_edit_info)

    # ৮. মেস নোটস
    elif call.data == "btn_notes":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, "📝 **মেস নোট:** তারিখসহ গুরুত্বপূর্ণ নোটটি লিখুন:")
        bot.register_next_step_handler(msg, process_add_note)

    # ৯. হিস্টোরি/লগ
    elif call.data == "btn_history":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        if not mess_data['history']:
            text = "📜 এখনো কোনো হিস্টোরি রেকর্ড করা হয়নি।"
        else:
            text = "📜 **হিসাব ও সংশোধনের হিস্টোরি:**\n\n" + "\n".join(mess_data['history'])
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    # ১০. মেস রিসিট
    elif call.data == "btn_receipt":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        total_meals = sum(mess_data['meals'].values())
        rate = mess_data['bazar_cost'] / total_meals if total_meals > 0 else 0
        receipt = f"📄 **মেসের চূড়ান্ত হিসাব রিসিট** 📄\n"
        receipt += f"🏢 মেস: {mess_data['mess_name']}\n"
        receipt += f"💵 মোট বাজার: {mess_data['bazar_cost']} টাকা\n"
        receipt += f"🍽 মোট মিল: {total_meals}\n"
        receipt += f"📈 মিল রেট: {rate:.2f}\n\n"
        receipt += "**মেম্বারদের বিস্তারিত:**\n"
        for name in mess_data['members']:
            cost = mess_data['meals'][name] * rate
            receipt += f"- {name}: মিল {mess_data['meals'][name]}টি, জমা {mess_data['balances'][name]} টাকা\n"
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, receipt, reply_markup=markup, parse_mode="Markdown")

    # --- সাব-বাটন অ্যাকশন ---
    elif call.data.startswith("addmeal_"):
        name = call.data.split("_")[1]
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, f"🍽 {name} এর আজকের মোট মিল সংখ্যা লিখুন (যেমন: 2):")
        bot.register_next_step_handler(msg, lambda m: save_meal(m, name))
        
    elif call.data.startswith("addbal_"):
        name = call.data.split("_")[1]
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, f"💰 {name} কত টাকা জমা দিয়েছেন তা লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_balance(m, name))

    elif call.data == "bazar_add":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, "🛒 বাজারের মোট টাকা এবং কী কী কেনা হয়েছে লিখুন:\n(যেমন: ৫০০, চাল ও তেল)")
        bot.register_next_step_handler(msg, save_bazar)

    elif call.data == "bazar_baki_add":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, "🔴 কত টাকা বাজার বাকি হয়েছে তা লিখুন:")
        bot.register_next_step_handler(msg, save_baki)

    elif call.data == "bazar_pay":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, "🟢 কত টাকা বাকি পরিশোধ করেছেন তা লিখুন:")
        bot.register_next_step_handler(msg, pay_baki)

    elif call.data == "khala_add":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        msg = bot.send_message(chat_id, "👩‍🍳 খালার মোট বিলের পরিমাণ লিখুন:")
        bot.register_next_step_handler(msg, save_khala_bill)

    elif call.data == "khala_paid_list":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        paid = "\n".join(mess_data['khala_paid']) if mess_data['khala_paid'] else "কেউ দেয়নি।"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, f"✅ **বিল পরিশোধিত মেম্বারদের তালিকা:**\n{paid}", reply_markup=markup)

    elif call.data == "khala_unpaid_list":
        try: bot.delete_message(chat_id, message_id)
        except: pass
        unpaid = [m for m in mess_data['members'] if m not in mess_data['khala_paid']]
        unpaid_text = "\n".join(unpaid) if unpaid else "সবাই পরিশোধ করেছে!"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, f"❌ **বিল অপরিশোধিত মেম্বারদের তালিকা:**\n{unpaid_text}", reply_markup=markup)

    elif call.data.startswith("kpaid_"):
        name = call.data.split("_")[1]
        if name not in mess_data['khala_paid']:
            mess_data['khala_paid'].append(name)
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(chat_id, f"✅ {name} এর খালার বিল পেইড হিসেবে চিহ্নিত হয়েছে।", reply_markup=markup)


# --- ডেটা সংরক্ষণ ফাংশন ---
def save_meal(message, name):
    try:
        val = float(message.text)
        mess_data['meals'][name] += val
        mess_data['history'].append(f"🍽 {name} এর {val}টি মিল যোগ করা হয়েছে।")
        bot.reply_to(message, f"✅ {name} এর {val}টি মিল সফলভাবে যোগ হয়েছে।")
        show_dashboard(message)
    except:
        bot.reply_to(message, "⚠️ ভুল ইনপুট। আবার চেষ্টা করুন।")

def save_balance(message, name):
    try:
        val = float(message.text)
        mess_data['balances'][name] += val
        mess_data['history'].append(f"💰 {name} এর {val} টাকা জমা হয়েছে।")
        bot.reply_to(message, f"✅ {name} এর {val} টাকা অ্যাড হয়েছে।")
        show_dashboard(message)
    except:
        bot.reply_to(message, "⚠️ ভুল ইনপুট।")

def save_bazar(message):
    try:
        cost = float(message.text.split(",")[0])
        note = message.text.split(",")[1] if "," in message.text else "বাজার"
        mess_data['bazar_cost'] += cost
        mess_data['bazar_list'].append(f"{cost} টাকা: {note}")
        mess_data['history'].append(f"🛒 {cost} টাকার বাজার খরচ যোগ হয়েছে।")
        bot.reply_to(message, "✅ বাজার খরচ সফলভাবে যোগ হয়েছে।")
        show_dashboard(message)
    except:
        bot.reply_to(message, "⚠️ ভুল ইনপুট। (যেমন: ৫০০, চাল)")

def save_baki(message):
    try:
        val = float(message.text)
        mess_data['bazar_baki'] += val
        mess_data['history'].append(f"🔴 {val} টাকা বাজার বাকি হয়েছে।")
        bot.reply_to(message, "✅ বাজার বাকি যোগ হয়েছে।")
        show_dashboard(message)
    except:
        bot.reply_to(message, "⚠️ শুধু সংখ্যা দিন।")

def pay_baki(message):
    try:
        val = float(message.text)
        mess_data['bazar_baki'] -= val
        mess_data['bazar_cost'] += val
        mess_data['history'].append(f"🟢 {val} টাকা বাকি পরিশোধ করা হয়েছে।")
        bot.reply_to(message, "✅ বাকি পরিশোধের হিসাব যুক্ত হয়েছে।")
        show_dashboard(message)
    except:
        bot.reply_to(message, "⚠️ শুধু সংখ্যা দিন।")

def save_khala_bill(message):
    try:
        mess_data['khala_bill'] = float(message.text)
        markup = InlineKeyboardMarkup(row_width=1)
        for name in mess_data['members']:
            markup.add(InlineKeyboardButton(name, callback_data=f"kpaid_{name}"))
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.send_message(message.chat.id, "✅ খালার বিল যুক্ত হয়েছে। যারা বিল দিয়েছে তাদের টিক দিন:", reply_markup=markup)
    except:
        bot.reply_to(message, "⚠️ শুধু সংখ্যা দিন।")

def process_edit_info(message):
    try:
        name, val = message.text.split(",")
        name = name.strip()
        val = float(val)
        if name in mess_data['members']:
            mess_data['meals'][name] = val
            mess_data['history'].append(f"✏️ {name} এর মিল সংশোধন করে {val} করা হয়েছে।")
            bot.reply_to(message, f"✅ {name} এর তথ্য সংশোধন করে {val} করা হয়েছে।")
            show_dashboard(message)
        else:
            bot.reply_to(message, "⚠️ মেম্বার খুঁজে পাওয়া যায়নি।")
    except:
        bot.reply_to(message, "⚠️ ফরম্যাট ভুল! (যেমন: Arafat, 12)")

def process_add_note(message):
    mess_data['notes'].append(message.text)
    mess_data['history'].append(f"📝 নতুন নোট যুক্ত করা হয়েছে।")
    bot.reply_to(message, "✅ নোট সফলভাবে সেভ হয়েছে।")
    show_dashboard(message)

# --- AI Chat Handler ---
@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    if not mess_data['mess_name']:
        bot.reply_to(message, "⚠️ আপনার মেস সেটআপ করা নেই। দয়া করে প্রথমে /start কমান্ড দিন।")
        return

    user_query = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    
    system_prompt = f"""
    You are an intelligent Mess Manager AI. Answer the user's questions in Bengali politely.
    Here is the current mess data:
    - Mess Name: {mess_data['mess_name']}
    - Manager Name: {mess_data['manager_name']}
    - Start Date: {mess_data['start_date']}
    - Member List: {mess_data['members']}
    - Meal Data: {mess_data['meals']}
    - Member Balances: {mess_data['balances']}
    - Total Bazar Cost: {mess_data['bazar_cost']}
    - Notes: {mess_data['notes']}
    """
    
    try:
        response = ai_model.generate_content([system_prompt, user_query])
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 ড্যাশবোর্ড / হোম", callback_data="go_to_home"))
        bot.reply_to(message, response.text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "🤖 AI রেসপন্স করতে পারছে না।")

# --- Bot Polling ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    print("AI-Powered Mess Bot updated and running perfectly...")
    bot.infinity_polling()
    
