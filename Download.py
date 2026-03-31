import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# الإعدادات
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_API_KEY)

# استخدام موديل Pro لأنه الأكثر توافقاً مع الحسابات المجانية
ai_model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📖 قراءة قصة", callback_data="gen")]]
    await update.message.reply_text("✨ أهلاً بك! اضغط للبدء.", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "gen":
        await query.edit_message_text("⏳ جاري التأليف من كاليفورنيا... ✨")
        try:
            # طلب قصة قصيرة
            response = ai_model.generate_content("اكتب قصة قصيرة جداً ومشوقة")
            text = response.text
        except Exception as e:
            text = f"⚠️ عذراً، حدث ضغط على السيرفر. حاول مجدداً.\n(Error: {str(e)[:50]})"

        keyboard = [[InlineKeyboardButton("🔄 قصة أخرى", callback_data="gen")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling(drop_pending_updates=True) # إضافة هذا الخيار لحل مشكلة التعليق
