import sys
import time
import sqlite3
import requests

# ---------------- CONFIG & TOKEN ----------------
# আপনার বট ফাদারের স্ক্রিনশট থেকে নেওয়া আসল টোকেন সরাসরি এখানে দেওয়া হলো
TOKEN = "8581132689:AAF_x23qBXyzAjpckVTX602J80MSe8Pk0Oc"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# ---------------- DATABASE ----------------
def db():
    return sqlite3.connect("mess.db")

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    conn.commit()
    conn.close()

init_db()

# ---------------- REQUESTS HELPERS ----------------
def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API_URL}/sendMessage", json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API_URL}/editMessageText", json=payload)
    except Exception as e:
        print(f"Error editing message: {e}")

def answer_callback(callback_query_id):
    try:
        requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id})
    except Exception as e:
        print(f"Error answering callback: {e}")

# ---------------- FLOW CONTROLLER ----------------
# ইউজারের বর্তমান স্টেট মনে রাখার জন্য মেমোরি ডিকশনারি
user_states = {}

def handle_text(chat_id, text):
    text = text.strip()
    state = user_states.get(chat_id, {}).get("state", "START")
    data = user_states.setdefault(chat_id, {"meals": [], "members": []})

    if text == "/start":
        user_states[chat_id] = {"state": "SET_NAME", "meals": [], "members": []}
        send_message(chat_id, "👋 Welcome!\n\n<b>মেসের নাম লিখো:</b>")
        return

    if state == "SET_NAME":
        data["mess_name"] = text
        data["state"] = "SET_MEALS"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🌅 সকাল", "callback_data": "sokal"},
                 {"text": "🌞 দুপুর", "callback_data": "dupur"},
                 {"text": "🌙 রাত", "callback_data": "rat"}],
                [{"text": "✅ Done", "callback_data": "done"}]
            ]
        }
        send_message(chat_id, "🍽️ <b>কয় বেলা মিল?</b> (নিচ থেকে সিলেক্ট করুন)", reply_markup=keyboard)

    elif state == "SET_MANAGER":
        data["manager"] = text
        data["state"] = "SET_DATE"
        send_message(chat_id, "📅 <b>Start date (তারিখ লিখুন):</b>")

    elif state == "SET_DATE":
        data["date"] = text
        data["state"] = "SET_MEMBER_COUNT"
        send_message(chat_id, "👥 <b>কয়জন member? (সংখ্যায় লিখুন):</b>")

    elif state == "SET_MEMBER_COUNT":
        try:
            count = int(text)
            data["count"] = count
            data["idx"] = 1
            data["state"] = "SET_MEMBERS"
            send_message(chat_id, "✍️ <b>(01) নাম লিখো:</b>")
        except ValueError:
            send_message(chat_id, "❌ অনুগ্রহ করে সংখ্যায় লিখুন (যেমন: ৫)")

    elif state == "SET_MEMBERS":
        idx = data["idx"]
        total = data["count"]
        data["members"].append(text)
        
        send_message(chat_id, f"({idx:02d}) {text} ✅")

        if idx < total:
            data["idx"] += 1
            next_idx = data["idx"]
            send_message(chat_id, f"✍️ <b>({next_idx:02d}) নাম লিখো:</b>")
        else:
            # ডাটাবেজে সেভ করা
            conn = db()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO settings VALUES('mess_name',?)", (data["mess_name"],))
            c.execute("INSERT OR REPLACE INTO settings VALUES('manager',?)", (data["manager"],))
            c.execute("INSERT OR REPLACE INTO settings VALUES('meals',?)", (",".join(data["meals"]),))
            c.execute("INSERT OR REPLACE INTO settings VALUES('date',?)", (data["date"],))

            for m in data["members"]:
                c.execute("INSERT INTO members(name) VALUES(?)", (m,))

            conn.commit()
            conn.close()

            send_message(chat_id, "🎉 <b>Setup Complete! আপনার মেস সফলভাবে তৈরি হয়েছে।</b>")
            user_states.pop(chat_id, None)

def handle_callback(chat_id, message_id, callback_id, query_data):
    answer_callback(callback_id)
    data = user_states.get(chat_id)
    
    if not data or data.get("state") != "SET_MEALS":
        return

    meals = data["meals"]
    mapping = {"sokal": "সকাল", "dupur": "দুপুর", "rat": "রাত"}

    if query_data in mapping:
        meal = mapping[query_data]
        if meal in meals:
            meals.remove(meal)
        else:
            meals.append(meal)

        # বাটন আপডেট
        keyboard = {
            "inline_keyboard": [
                [{"text": "🌅 সকাল" + (" ✅" if "সকাল" in meals else ""), "callback_data": "sokal"},
                 {"text": "🌞 দুপুর" + (" ✅" if "দুপুর" in meals else ""), "callback_data": "dupur"},
                 {"text": "🌙 রাত" + (" ✅" if "রাত" in meals else ""), "callback_data": "rat"}],
                [{"text": "✅ Done", "callback_data": "done"}]
            ]
        }
        current_selection = ', '.join(meals) if meals else "কিছুই না"
        edit_message(chat_id, message_id, f"🍽️ Selected: {current_selection}\n\nসব নির্বাচন শেষে Done চাপো", reply_markup=keyboard)

    elif query_data == "done":
        if not meals:
            send_message(chat_id, "⚠️ কমপক্ষে ১টা বেলা সিলেক্ট করো!")
            return
        
        data["state"] = "SET_MANAGER"
        send_message(chat_id, "👤 <b>Manager নাম লিখো:</b>")

# ---------------- POLLING (MAIN) ----------------
def main():
    print("বটটি এখন সচল আছে... (Polling Mode)")
    offset = 0
    while True:
        try:
            response = requests.get(f"{API_URL}/getUpdates", params={"offset": offset, "timeout": 30})
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    # টেক্সট মেসেজ হ্যান্ডেল করা
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        handle_text(chat_id, text)
                    
                    # বাটন ক্লিক হ্যান্ডেল করা
                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        chat_id = cb["message"]["chat"]["id"]
                        message_id = cb["message"]["message_id"]
                        callback_id = cb["id"]
                        query_data = cb["data"]
                        handle_callback(chat_id, message_id, callback_id, query_data)
        except KeyboardInterrupt:
            print("\nবট বন্ধ করা হয়েছে।")
            sys.exit(0)
        except Exception as e:
            print(f"Error in polling: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
          
