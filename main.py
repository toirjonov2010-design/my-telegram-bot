import os
import time
import threading
from flask import Flask
import telebot
from telebot import types

# Render serveri uchun veb-server (keep-alive)
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

# BOT SOZLAMALARI
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_data = {}

# ASOSIY MENYU TUGMALARI
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

# 1. /start KOMANDASI
@bot.message_handler(commands=['start'])
def start_command(message):
    first_name = message.from_user.first_name or "O'quvchi"
    text = (
        f"👋 **Salom, {first_name}!**\n\n"
        f"IT ta'lim platformamizning rasmiy botiga xush kelibsiz!\n"
        f"Quyidagi menyudan o'zingizga kerakli bo'limni tanlang:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# 2. XABARLARNI QABUL QILISH
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

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
        payment_text = (
            "💳 **To'lov holatingiz:**\n\n"
            "✅ **Holat:** Siz to'lovni amalga oshirgansiz!\n"
            "💰 **Qarzdorlik:** `0 so'm`\n\n"
            "--- \n"
            "⚠️ _Agar to'lov qilmagan bo'lsangiz:_\n"
            "❌ **To'lovni amalga oshiring:** Qarzdorlik `100 000 so'm`"
        )
        bot.send_message(chat_id, payment_text, parse_mode="Markdown")

    else:
        bot.send_message(chat_id, "Iltimos, quyidagi menyudan birini tanlang 👇", reply_markup=main_menu())

# RO'YXATDAN O'TISH BOSQICHLARI
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

    success_text = (
        "🎉 **Muvaffaqiyatli ro'yxatdan o'tdingiz!**\n\n"
        f"👤 **Ism-Familiya:** {full_name}\n"
        f"📞 **Telefon:** {phone}\n\n"
        "Tashakkur! Tez orada siz bilan bog'lanamiz."
    )
    
    bot.send_message(chat_id, success_text, parse_mode="Markdown", reply_markup=main_menu())

# BOTNI ISHGA TUSHIRISH (24/7)
if __name__ == '__main__':
    keep_alive()
    print("Bot 24/7 serverda ishga tushdi...")
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Xatolik: {e}")
            time.sleep(5)