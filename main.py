import os
import time
import threading
import sqlite3
from flask import Flask
import telebot
from telebot import types

app = Flask('')

@app.route('/')
def home():
    return "Bot 24/7 rejimda ishlayapti!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

DB_NAME = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                full_name TEXT,
                phone TEXT,
                username TEXT,
                is_paid INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init xatosi: {e}")

def save_user(chat_id, full_name, phone, username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (chat_id, full_name, phone, username)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                full_name=COALESCE(EXCLUDED.full_name, users.full_name),
                phone=COALESCE(EXCLUDED.phone, users.phone),
                username=COALESCE(EXCLUDED.username, users.username)
        ''', (chat_id, full_name, phone, username))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save User xatosi: {e}")

def get_all_registered():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, full_name, phone, username, is_paid FROM users')
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for r in rows:
            chat_id = r[0]
            full_name = str(r[1]) if r[1] else "To'liq ro'yxatdan o'tmagan"
            phone = str(r[2]) if r[2] else "Kiritilmagan"
            username = str(r[3]) if r[3] else ""
            is_paid = r[4] if r[4] is not None else 0
            result.append((chat_id, full_name, phone, username, is_paid))
            
        return result
    except Exception as e:
        print(f"Get All xatosi: {e}")
        return []

def get_user_payment_status(chat_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_paid FROM users WHERE chat_id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] is not None else 0
    except Exception as e:
        print(f"Payment Status xatosi: {e}")
        return 0

def mark_as_paid(chat_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_paid = 1 WHERE chat_id = ?', (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Mark Paid xatosi: {e}")
        return False

def delete_user(chat_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE chat_id = ?', (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Delete User xatosi: {e}")
        return False

def get_all_chat_ids():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM users')
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows if r[0] is not None]
    except Exception as e:
        print(f"Get Chat IDs xatosi: {e}")
        return []

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [7612340447, 443328100]
user_data = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📚 Bizning kurs haqida")
    btn2 = types.KeyboardButton("📞 Biz bilan bog'lanish")
    btn3 = types.KeyboardButton("🎥 Dars videolari")
    btn4 = types.KeyboardButton("📝 Kursga qo'shilish")
    btn5 = types.KeyboardButton("💳 To'lov holati")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("📢 Barcha o'quvchilarga xabar yuborish")
    btn2 = types.KeyboardButton("👥 O'quvchilarni boshqarish")
    btn3 = types.KeyboardButton("⬅️ Asosiy menyuga qaytish")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    save_user(message.chat.id, None, None, message.from_user.username)
    first_name = message.from_user.first_name or "O'quvchi"
    text = (
        f"👋 **Salom, {first_name}!**\n\n"
        f"IT ta'lim platformamizning rasmiy botiga xush kelibsiz!\n"
        f"Quyidagi menyudan o'zingizga kerakli bo'limni tanlang:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if is_admin(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "⚙️ **Admin paneliga xush kelibsiz!**\nQuyidagi amallardan birini tanlang:", 
            parse_mode="Markdown", 
            reply_markup=admin_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Siz administrator emassiz!")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    if is_admin(user_id):
        if text == "📢 Barcha o'quvchilarga xabar yuborish":
            msg = bot.send_message(chat_id, "📝 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing:", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, send_broadcast)
            return

        elif text == "👥 O'quvchilarni boshqarish":
            users = get_all_registered()
            if not users:
                bot.send_message(chat_id, "📭 Hozircha hech kim ro'yxatdan o'tmagan.", reply_markup=admin_menu())
            else:
                bot.send_message(chat_id, f"📋 **Barcha foydalanuvchilar va o'quvchilar ro'yxati ({len(users)} kishi):**", parse_mode="Markdown")
                for u in users:
                    try:
                        u_chat_id, full_name, phone, username, is_paid = u
                        status_str = "✅ To'lov qilgan" if is_paid == 1 else "❌ To'lov qilmagan"
                        username_str = f"@{username}" if username else "Mavjud emas"
                        
                        user_info = (
                            f"👤 **Ism-Familiya:** {full_name}\n"
                            f"📞 **Telefon:** {phone}\n"
                            f"💬 **User:** {username_str}\n"
                            f"💳 **To'lov:** {status_str}\n"
                            f"🆔 **ID:** `{u_chat_id}`"
                        )
                        
                        inline_kb = types.InlineKeyboardMarkup(row_width=1)
                        if is_paid == 0:
                            btn_pay = types.InlineKeyboardButton("✅ To'lov qildi deb belgilash", callback_data=f"pay_{u_chat_id}")
                            inline_kb.add(btn_pay)
                        
                        btn_del = types.InlineKeyboardButton("❌ Chiqarib yuborish", callback_data=f"del_{u_chat_id}")
                        inline_kb.add(btn_del)
                        
                        bot.send_message(chat_id, user_info, parse_mode="Markdown", reply_markup=inline_kb)
                    except Exception as e:
                        print(f"Foydalanuvchini chiqarishda xatolik: {e}")
            return

        elif text == "⬅️ Asosiy menyuga qaytish":
            bot.send_message(chat_id, "Asosiy menyudasiz:", reply_markup=main_menu())
            return

    if text == "📚 Bizning kurs haqida":
        info_text = (
            "✨ **IT Savodxonligi Kursi Haqida:**\n\n"
            "💻 **Noldan boshlanadigan ta'lim:**\n"
            "└ _Hech qanday boshlang'ich bilim talab etilmaydi!_\n\n"
            "🚀 **Amaliy va intensiv yondashuv:**\n"
            "└ _Har bir dars real mashqlar va kompyuterlarda amaliy topshiriqlar asosida o'tiladi._\n\n"
            "👨‍🏫 **Individual yondashuv:**\n"
            "└ _Har bir o'quvchining o'zlashtirishiga alohida e'tibor qaratiladi._\n\n"
            "📜 **Zamonaviy sharoitlar va sertifikat:**\n"
            "└ _Kurs yakunida bitiruvchilarga maxsus sertifikat taqdim etiladi!_"
        )
        bot.send_message(chat_id, info_text, parse_mode="Markdown")

    elif text == "📞 Biz bilan bog'lanish":
        contact_text = (
            "📞 **Biz bilan bog'lanish:**\n\n"
            "👨‍🏫 **Mas'ul xodimlar:**\n"
            "• Qodirboyev Xudobergan: +998 90 560 59 59\n"
            "• Eraliyev Hayot: +998 97 957 54 55\n\n"
            "❓ Savollaringiz bo'lsa, bemalol qo'ng'iroq qilishingiz mumkin!"
        )
        bot.send_message(chat_id, contact_text, parse_mode="Markdown")

    elif text == "🎥 Dars videolari":
        inline_markup = types.InlineKeyboardMarkup()
        btn_link = types.InlineKeyboardButton("🔗 Kanalga o'tish", url="https://t.me/+6VsJbiT7u340ZWQy")
        inline_markup.add(btn_link)

        video_text = (
            "🎥 **Dars Videolari:**\n\n"
            "Barcha o'quv video darsliklarimiz maxsus Telegram kanalimizga joylab boriladi.\n"
            "Kanalga kirish uchun quyidagi tugmani bosing 👇"
        )
        bot.send_message(chat_id, video_text, parse_mode="Markdown", reply_markup=inline_markup)

    elif text == "📝 Kursga qo'shilish":
        msg = bot.send_message(
            chat_id, 
            "📋 **Kursga ro'yxatdan o'tish:**\n\nIltimos, **Ism va Familiyangizni** yozib yuboring:\n_(Masalan: Ozodbek Toirjonov)_",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, get_full_name)

    elif text == "💳 To'lov holati":
        is_paid = get_user_payment_status(chat_id)
        if is_paid == 1:
            payment_text = "✅ **Siz to'lovni amalga oshirgansiz!**"
        else:
            payment_text = "❌ **Siz hali to'lov qilmagansiz!**"
        bot.send_message(chat_id, payment_text, parse_mode="Markdown")

    else:
        bot.send_message(chat_id, "Iltimos, quyidagi menyudan birini tanlang 👇", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return

    if call.data.startswith("del_"):
        target_chat_id = int(call.data.split("_")[1])
        if delete_user(target_chat_id):
            bot.answer_callback_query(call.id, "O'quvchi bazadan o'chirildi!")
            bot.edit_message_text(f"❌ **Ushbu o'quvchi bazadan chiqarib yuborildi.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "Xatolik yuz berdi!")

    elif call.data.startswith("pay_"):
        target_chat_id = int(call.data.split("_")[1])
        if mark_as_paid(target_chat_id):
            bot.answer_callback_query(call.id, "To'lov tasdiqlandi!")
            bot.edit_message_text(f"✅ **Ushbu o'quvchi to'lovni amalga oshirdi deb belgilandi!**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            admin_msg = f"💳 **ADMIN XABARI:**\n\nID: `{target_chat_id}` bo'lgan o'quvchi **to'lovni amalga oshirdi!**"
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
                except Exception:
                    pass

def get_full_name(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'name': message.text}

    phone_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_phone = types.KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True)
    phone_markup.add(btn_phone)

    msg = bot.send_message(
        chat_id, 
        f"Rahmat, **{message.text}**!\n\nEndi esa **telefon raqamingizni** yuboring (pastdagi tugmani bosing yoki yozib yuboring):", 
        parse_mode="Markdown",
        reply_markup=phone_markup
    )
    bot.register_next_step_handler(msg, get_phone_number)

def get_phone_number(message):
    chat_id = message.chat.id
    
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    full_name = user_data.get(chat_id, {}).get('name', 'Noma\'lum')
    username = message.from_user.username or ""

    save_user(chat_id, full_name, phone, username)

    success_text = (
        "🎉 **Muvaffaqiyatli ro'yxatdan o'tdingiz!**\n\n"
        f"👤 **Ism-Familiya:** {full_name}\n"
        f"📞 **Telefon:** {phone}\n\n"
        "Tashakkur! Tez orada siz bilan bog'lanamiz."
    )
    bot.send_message(chat_id, success_text, parse_mode="Markdown", reply_markup=main_menu())

    username_str = f"@{username}" if username else "Mavjud emas"
    admin_notification = (
        "📥 **YANGI O'QUVCHI RO'YXATDAN O'TDI!**\n\n"
        f"👤 **Ism-Familiya:** {full_name}\n"
        f"📞 **Telefon:** {phone}\n"
        f"💬 **Telegram profil:** {username_str}\n"
        f"🆔 **ID:** `{chat_id}`"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, admin_notification, parse_mode="Markdown")
        except Exception as e:
            print(f"Adminga xabar yuborishda xatolik: {e}")

def send_broadcast(message):
    broadcast_text = message.text
    chat_ids = get_all_chat_ids()
    count = 0
    for cid in chat_ids:
        try:
            bot.send_message(cid, f"📢 **ADMIN XABARI:**\n\n{broadcast_text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
            
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, f"✅ Xabar {count} ta foydalanuvchiga yuborildi!", reply_markup=admin_menu())
        except Exception:
            pass

if __name__ == '__main__':
    init_db()
    keep_alive()
    print("Bot 24/7 serverda ishga tushdi...")
    while True:
        try:
            bot.polling(non_stop=True, interval=2, timeout=30)
        except Exception as e:
            print(f"Aloqa xatosi: {e}")
            time.sleep(5)