import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- بياناتك ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_API_KEY)

# مصفوفة موديلات للتجربة التلقائية
def setup_ai():
    for model_name in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro', 'models/gemini-pro']:
        try:
            m = genai.GenerativeModel(model_name)
            # تجربة فحص سريعة جداً
            m.generate_content("Hi", generation_config={"max_output_tokens": 1})
            return m
        except: continue
    return None

ai_model = setup_ai()

# قصص احتياطية في حال تعطل السيرفر لضمان استمرارية البوت
backup_stories = [
    "📜 في أعماق المحيط، وجد غواص صندوقاً قديماً لا يفتح إلا بكلمة صدق.. وعندما نطق بها، انفتح ليظهر مرآة تري الشخص أجمل ما فيه وليس شكله فقط.",
    "📜 كان هناك مزارع يزرع الأمل في قلوب الناس، كلما ابتسم لشخص، نبتت زهرة في طريق ذلك الشخص في اليوم التالي.",
    "📜 يحكى أن النجوم هي ثقوب في رداء الليل، تتسلل منها أحلامنا التي لم تتحقق بعد لتنير درب الضائعين."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # استخدام callback_data قصيرة جداً لتجنب خطأ Button_data_invalid
    keyboard = [[InlineKeyboardButton("📖 قراءة قصة", callback_data="gen_story")]]
    await update.message.reply_text("✨ أهلاً بك في بوت القصص الذكي.\n\nاضغط على الزر لتأليف قصة جديدة فوراً!", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "gen_story":
        await query.edit_message_text("⏳ جاري استدعاء الخيال... انتظر ثواني ✨")
        
        try:
            if ai_model:
                # طلب قصة مباشرة وقصيرة لضمان السرعة
                response = ai_model.generate_content("اكتب قصة قصيرة جداً ومشوقة مع ايموجي")
                text = response.text
            else:
                raise Exception("No Model")
        except:
            # استخدام قصة احتياطية إذا فشل الذكاء الاصطناعي
            import random
            text = random.choice(backup_stories) + "\n\n(ملاحظة: هذه قصة من الأرشيف بسبب ضغط السيرفر)"

        keyboard = [[InlineKeyboardButton("🔄 قصة أخرى", callback_data="gen_story")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
