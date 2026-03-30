import telebot
import yt_dlp
import os
from telebot import types

TOKEN = "8646400281:AAFQAejRPcDfpGnBreUFziNzix0m7D8DKuA"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🛡️ **هـلا بـيـك يـا {user_name} فـي بـوت [ فـزعـة ]** 🛡️\n\n"
        "أرسل الرابط الآن.."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if not url.startswith("http"):
        bot.reply_to(message, "⚠️ أرسل رابط صحيح!")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_video = types.InlineKeyboardButton("🔴 فيديو", callback_data=f"video|{url}")
    btn_audio = types.InlineKeyboardButton("🔵 صوت", callback_data=f"audio|{url}")
    markup.add(btn_video, btn_audio)
    bot.reply_to(message, "اختر النوع: 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data.split("|")
    action, url = data[0], data[1]
    bot.edit_message_text("⚡ **فـزعـة جاري التحميل...**", call.message.chat.id, call.message.message_id)

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'Faz3a_{call.from_user.id}.%(ext)s',
        'no_warnings': True,
        'quiet': True,
        'nocheckcertificate': True,
        # الخدعة الجديدة: التنكر بهيئة YouTube TV لتخطي طلب تسجيل الدخول
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'web_embedded'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }

    if action == 'audio':
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as f:
            if action == 'video':
                bot.send_video(call.message.chat.id, f, caption="تم بواسطة فزعة 🛡️")
            else:
                bot.send_audio(call.message.chat.id, f, caption="تم بواسطة فزعة 🛡️")
        os.remove(filename)
    except Exception as e:
        # إذا فشل يوتيوب، سنخبر المستخدم أن يجرب روابط أخرى
        bot.send_message(call.message.chat.id, "❌ يوتيوب حالياً يطلب تسجيل دخول لسيرفراتنا. جرب روابط تيك توك أو فيسبوك، فهي تعمل 100%!")

bot.polling(none_stop=True)
