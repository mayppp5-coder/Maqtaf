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

# محاولة اختيار موديل متاح
def get_model():
    for m in ['gemini-1.5-flash', 'gemini-pro', 'models/gemini-1.5-flash']:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("hi", generation_config={"max_output_tokens": 1})
            return model
        except: continue
    return None

ai_model = get_model()

async def get_ai_response(prompt):
    if not ai_model: return "❌ فشل الاتصال بالذكاء الاصطناعي."
    try:
        response = ai_model.generate_content(prompt)
        return response.text if response.text else "تعذر تأليف القصة."
    except Exception as e:
        return f"⚠️ خطأ: {str(e)[:50]}"

# --- وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # نستخدم "read_now" كبيانات ثابتة للزر لتجنب خطأ الحجم
    keyboard = [[InlineKeyboardButton("📖 قراءة قصة جديدة", callback_data="read_now")],
                [InlineKeyboardButton("🔄 تغيير الموضوع", callback_data="start_again")]]
    await update.message.reply_text("✨ أهلاً بك! هل أنت مستعد لقصة ذكاء اصطناعي مشوقة؟", 
                                  reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data in ["read_now", "start_again"]:
        await query.edit_message_text("⏳ جاري التأليف... انتظر قليلاً ✨")
        
        # نطلب من الذكاء الاصطناعي تأليف قصة مباشرة
        story = await get_ai_response("اكتب قصة قصيرة جدا ومشوقة مع عنوان جذاب وايموجي")
        
        keyboard = [[InlineKeyboardButton("🔄 قصة أخرى", callback_data="read_now")]]
        
        # إرسال القصة في رسالة جديدة لضمان عدم حدوث خطأ في الطول
        await query.message.reply_text(f"{story}", 
                                       reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
