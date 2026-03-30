import telebot
import yt_dlp
import os

# ضع توكن البوت الجديد الذي أنشأته من BotFather هنا
TOKEN ="8646400281:AAFQAejRPcDfpGnBreUFziNzix0m7D8DKuA"


bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت مقطف! 🚀\n\n"
        "أنا مساعدك الذكي لتحميل الفيديوهات من:\n"
        "✅ تيك توك | ✅ إنستقرام | ✅ يوتيوب\n\n"
        "فقط أرسل لي رابط الفيديو، واترك الباقي عليّ! 😎"
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # التأكد أن الرسالة تحتوي على رابط
    if not url.startswith("http"):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح 🔗")
        return

    sent_msg = bot.reply_to(message, "جاري المعالجة والتحميل.. انتظر قليلاً ⏳")

    # إعدادات المكتبة لتحميل أفضل جودة بصيغة mp4
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4', # اسم الملف المؤقت
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو بعد التحميل
        with open('video.mp4', 'rb') as video:
            bot.send_video(message.chat.id, video, caption="تم التحميل بنجاح ✅")
        
        # حذف الملف من جهازك (أو السيرفر) بعد الإرسال لتوفير المساحة
        os.remove('video.mp4')
        bot.delete_message(message.chat.id, sent_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"حدث خطأ أثناء التحميل: {e}", message.chat.id, sent_msg.message_id)

print("البوت يعمل الآن.. جرب إرسال رابط!")
bot.infinity_polling()
