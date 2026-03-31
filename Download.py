import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

# وظيفة ذكية لاختيار الموديل المتاح في حسابك
def get_working_model():
    # قائمة بأسماء الموديلات المحتملة حسب تحديثات جوجل
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-pro',
        'models/gemini-1.5-flash',
        'models/gemini-pro'
    ]
    for m in models_to_try:
        try:
            model = genai.GenerativeModel(m)
            # تجربة فحص بسيطة
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            logger.info(f"✅ الموديل الشغال هو: {m}")
            return model
        except:
            continue
    return None

ai_model = get_working_model()

async def get_ai_response(prompt):
    if not ai_model:
        return "❌ خطأ: لم يتم العثور على موديل شغال في حسابك. تأكد من تفعيل Gemini API."
    try:
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ عذراً، واجهت مشكلة: {str(e)[:100]}"

# --- وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = await get_ai_response("أعطني عنوان قصة قصير جدا (3 كلمات)")
    keyboard = [[InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
                [InlineKeyboardButton("🔄 عنوان آخر", callback_data="next")]]
    await update.message.reply_text(f"✨ هل تريد قصة اليوم؟\n\nالعنوان المقترح: **{title}**", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "next":
        title = await get_ai_response("عنوان قصة قصير جدا (3 كلمات)")
        keyboard = [[InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
                    [InlineKeyboardButton("🔄 قصة أخرى", callback_data="next")]]
        await query.edit_message_text(f"ما رأيك بهذا؟\n\n🔹 **{title}**", 
                                     reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif query.data.startswith("read|"):
        title = query.data.split("|")[1]
        await query.edit_message_text(f"⏳ جاري كتابة قصة: **{title}**...")
        story = await get_ai_response(f"اكتب قصة قصيرة جدا عن {title}")
        await query.message.reply_text(f"📖 **{title}**\n\n{story}", 
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 قصة جديدة", callback_data="next")]]), 
                                       parse_mode="Markdown")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
