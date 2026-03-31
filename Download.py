import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الشخصية ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد الذكاء الاصطناعي - تعديل اسم الموديل ليتوافق مع التحديث الأخير
genai.configure(api_key=GEMINI_API_KEY)

# جربنا flash وإذا فشل سيحول تلقائياً لـ pro
MODEL_NAME = 'models/gemini-1.5-flash' 

try:
    ai_model = genai.GenerativeModel(MODEL_NAME)
    logger.info(f"تم تحميل الموديل {MODEL_NAME} بنجاح")
except Exception as e:
    logger.error(f"فشل تحميل الموديل الأساسي: {e}")
    ai_model = genai.GenerativeModel('models/gemini-pro')

# --- وظائف التوليد ---

async def get_ai_title():
    try:
        # طلب عنوان بسيط جداً لتقليل وقت الاستجابة
        response = ai_model.generate_content("أعطني عنوان قصة مشوق ومختصر (3 كلمات فقط)")
        return response.text.strip()
    except Exception as e:
        logger.error(f"خطأ في العنوان: {e}")
        return "سر الغابة المفقودة"

async def get_ai_story(title):
    try:
        # طلب قصة قصيرة لضمان عدم حدوث Timeout في السيرفر
        prompt = f"اكتب قصة قصيرة جداً ومشوقة عن: {title}. استخدم ايموجي."
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"خطأ في القصة: {e}")
        return "عذراً، يبدو أن جنيّ القصص نائم الآن! حاول مرة أخرى بعد قليل. 🌙"

# --- وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = await get_ai_title()
    keyboard = [
        [InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
        [InlineKeyboardButton("🔄 أريد عنواناً آخر", callback_data="next")]
    ]
    await update.message.reply_text(
        f"✨ أهلاً بك في عالم القصص!\n\nلقد اخترت لك: **{title}**\nهل ترغب في قراءتها؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "next":
        title = await get_ai_title()
        keyboard = [
            [InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
            [InlineKeyboardButton("🔄 قصة أخرى", callback_data="next")]
        ]
        await query.edit_message_text(
            f"ما رأيك بهذا العنوان؟\n\n🔹 **{title}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("read|"):
        title = query.data.split("|")[1]
        await query.edit_message_text(f"⏳ جاري تأليف قصة: **{title}**...")
        
        story_text = await get_ai_story(title)
        keyboard = [[InlineKeyboardButton("🔄 قصة جديدة", callback_data="next")]]
        
        # إرسال القصة في رسالة جديدة لتجنب مشاكل طول النص في edit_message
        await query.message.reply_text(
            f"📖 **{title}**\n\n{story_text}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# --- تشغيل البوت ---

if __name__ == '__main__':
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("🚀 البوت يعمل الآن...")
    application.run_polling()
