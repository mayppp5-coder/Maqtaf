import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات (بياناتك الخاصة) ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

# إعداد الذكاء الاصطناعي (تم استخدام flash للسرعة القصوى)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# إعداد السجلات (Logging) لمراقبة الأداء في Railway
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- وظائف توليد المحتوى ---

async def get_ai_title():
    """توليد عنوان قصة قصير جداً وسريع"""
    try:
        # طلب عنوان مختصر لضمان سرعة الاستجابة
        prompt = "أعطني عنوان قصة مشوق ومختصر جداً (3 كلمات فقط). بدون مقدمات."
        response = ai_model.generate_content(prompt)
        title = response.text.strip().replace("*", "").replace("#", "")
        return title if title else "سر الغابة المفقودة"
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "حكاية من وراء الأفق"

async def get_ai_story(title):
    """توليد القصة الكاملة بناءً على العنوان"""
    try:
        prompt = f"اكتب قصة قصيرة جداً ومثيرة بناءً على هذا العنوان: {title}. اجعلها مشوقة ومع ايموجي."
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        return "عذراً صديقي، يبدو أن جنيّ القصص مشغول الآن! حاول مرة أخرى بعد لحظات. 😅"

# --- وظائف التعامل مع البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند إرسال /start أو الدخول للبوت"""
    title = await get_ai_title()
    
    keyboard = [
        [InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
        [InlineKeyboardButton("🔄 أريد عنواناً آخر", callback_data="next")]
    ]
    
    await update.message.reply_text(
        "✨ أهلاً بك في بوت القصص الذكي!\n\n"
        "لقد اخترت لك هذا العنوان المشوق، هل ترغب في قراءتها؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer() # لإزالة علامة التحميل من زر التليجرام
    
    if query.data == "next":
        # توليد عنوان جديد فوراً
        title = await get_ai_title()
        keyboard = [
            [InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
            [InlineKeyboardButton("🔄 قصة أخرى", callback_data="next")]
        ]
        await query.edit_message_text(
            f"ما رأيك بهذا العنوان الجديد؟\n\n🔹 **{title}**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("read|"):
        title = query.data.split("|")[1]
        
        # رسالة مؤقتة تشعر المستخدم بأن البوت يعمل
        await query.edit_message_text(f"✍️ جاري كتابة قصة: **{title}**...\nلحظات قليلة من فضلك ✨")
        
        story_text = await get_ai_story(title)
        
        keyboard = [[InlineKeyboardButton("🔄 قصة جديدة", callback_data="next")]]
        
        # إرسال القصة النهائية
        await query.message.reply_text(
            f"📖 **{title}**\n\n{story_text}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# --- تشغيل المحرك ---

if __name__ == '__main__':
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("🚀 البوت انطلق الآن...")
    application.run_polling()
