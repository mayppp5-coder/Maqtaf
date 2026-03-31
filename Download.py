import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- البيانات ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

# إعداد الذكاء الاصطناعي مع إيقاف فلاتر الأمان (لضمان الاستجابة)
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {"temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 500}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

ai_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config=generation_config,
    safety_settings=safety_settings
)

async def get_ai_title():
    try:
        response = ai_model.generate_content("اعطني عنوان قصة قصير جدا (3 كلمات)")
        return response.text.strip() if response.text else "سر الغموض"
    except:
        return "حكاية غريبة"

async def get_ai_story(title):
    try:
        # إضافة تعليمات صريحة للذكاء الاصطناعي ليكون سريعاً
        response = ai_model.generate_content(f"اكتب قصة قصيرة جدا عن: {title}")
        if response.text:
            return response.text
        return "لم أستطع تأليف القصة، جرب عنواناً آخر."
    except Exception as e:
        print(f"Error: {e}")
        return "حدث خطأ في الاتصال بذكاء Google، حاول مرة أخرى."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = await get_ai_title()
    keyboard = [[InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
                [InlineKeyboardButton("🔄 عنوان آخر", callback_data="next")]]
    await update.message.reply_text("✨ هل تريد قصة اليوم؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "next":
        title = await get_ai_title()
        keyboard = [[InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
                    [InlineKeyboardButton("🔄 قصة أخرى", callback_data="next")]]
        await query.edit_message_text(f"العنوان: **{title}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif query.data.startswith("read|"):
        title = query.data.split("|")[1]
        await query.edit_message_text(f"⏳ جاري التأليف...")
        story = await get_ai_story(title)
        await query.message.reply_text(f"📖 **{title}**\n\n{story}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 قصة جديدة", callback_data="next")]]), parse_mode="Markdown")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
