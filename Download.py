import telebot
import yt_dlp
import os
from telebot import types

# التوكن الخاص بك
TOKEN = "8646400281:AAFQAejRPcDfpGnBreUFziNzix0m7D8DKuA"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
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

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_video = types.InlineKeyboardButton("🔴 تـحـمـيـل فـيـديـو (MP4) 🔴", callback_data=f"video|{url}")
    btn_audio = types.InlineKeyboardButton("🔵 تـحـمـيـل صـوت (MP3) 🔵", callback_data=f"audio|{url}")
    markup.add(btn_video, btn_audio)

    bot.reply_to(message, "تـم استلام الرابط! شـتـريد أحمل لك؟ 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data.split("|")
    action = data[0]
    url = data[1]
    
    bot.edit_message_text("⚡ **فـزعـة جاري التحميل... ثواني ويصلك**", call.message.chat.id, call.message.message_id)

    # إعدادات التحميل - تم تصحيح المسافات هنا بدقة
    ydl_opts = {
        # اختيار 'best' يحل مشكلة Requested format is not available
        'format': 'best',
        'outtmpl': f'Faz3a_{call.from_user.id}.%(ext)s',
        'no_warnings': True,
        'quiet': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web_embedded'],
            }
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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
            
            # معالجة اسم الملف في حال كان المطلوب صوتاً
            if action == 'audio':
                base, ext = os.path.splitext(filename)
                new_filename = base + '.mp3'
                # التأكد من تغيير اسم الملف يدوياً إذا لم يقم البرنامج بذلك
                if os.path.exists(new_filename):
                    filename = new_filename
                elif os.path.exists(base + '.webm'):
                     filename = base + '.webm' # في حال فشل التحويل مؤقتاً

        with open(filename, 'rb') as f:
            if action == 'video':
                bot.send_video(call.message.chat.id, f, caption="تم التحميل بواسطة بوت فزعة 🛡️")
            else:
                bot.send_audio(call.message.chat.id, f, caption="تم تحويل الصوت بواسطة بوت فزعة 🛡️")
        
        if os.path.exists(filename):
            os.remove(filename) 

    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg:
            bot.send_message(call.message.chat.id, "❌ يوتيوب طلب تسجيل دخول. جرب رابط آخر أو فيديو قصير.")
        else:
            bot.send_message(call.message.chat.id, f"❌ عذراً، صار خلل بالتحميل.\nالسبب: {error_msg[:100]}")

bot.polling(none_stop=True)
