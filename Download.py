
import telebot
import yt_dlp
import os
from telebot import types

# ضع التوكن الخاص بك هنا
TOKEN = "8646400281:AAFQAejRPcDfpGnBreUFziNzix0m7D8DKuA"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    # واجهة الترحيب باسم "فزعة" بشكل مميز
    welcome_text = (
        f"🛡️ **هـلا بـيـك يـا {user_name} فـي بـوت [ فـزعـة ]** 🛡️\n\n"
        "أنا فزعتك لتحميل أي فيديو يخطر ببالك من:\n"
        "تيك توك 🎶 | إنستقرام 📸 | يوتيوب 🎥 | فيسبوك 💙\n\n"
        "🚀 **طريقة الاستخدام:**\n"
        "أرسل الرابط هنا.. واترك الباقي على فزعة!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if not url.startswith("http"):
        bot.reply_to(message, "⚠️ يا طيب، أرسل رابط صحيح حتى أقدر أفزعلك!")
        return

    # إنشاء الأزرار الملونة بشكل مربعات واضحة
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # الزر الأحمر للفيديو
    btn_video = types.InlineKeyboardButton("🔴 تـحـمـيـل فـيـديـو (MP4) 🔴", callback_data=f"video|{url}")
    
    # الزر الأزرق للصوت
    btn_audio = types.InlineKeyboardButton("🔵 تـحـمـيـل صـوت (MP3) 🔵", callback_data=f"audio|{url}")
    
    markup.add(btn_video, btn_audio)

    bot.reply_to(message, "تـم استلام الرابط! شـتـريد أحمل لك؟ 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data.split("|")
    action = data[0]
    url = data[1]
    
    bot.edit_message_text("⚡ **فـزعـة جاري التحميل... ثواني ويصلك**", call.message.chat.id, call.message.message_id)

                ydl_opts = {
        'format': 'best',
        'outtmpl': f'Faz3a_{call.from_user.id}.%(ext)s',
        'no_warnings': True,
        'quiet': True,
        'nocheckcertificate': True,
        # هذه الإعدادات تجعل يوتيوب يظن أنك تطبيق موبايل رسمي
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        'postprocessor_args': [
            '-c:v', 'copy',
        ],
    }




    if action == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as f:
            if action == 'video':
                bot.send_video(call.message.chat.id, f, caption="تم التحميل بواسطة بوت فزعة 🛡️")
            else:
                bot.send_audio(call.message.chat.id, f, caption="تم تحويل الصوت بواسطة بوت فزعة 🛡️")
        
        os.remove(filename) 
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ عذراً، صار خلل بسيط بالتحميل. جرب رابط ثاني!")

bot.polling()
