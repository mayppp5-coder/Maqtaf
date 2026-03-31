import logging
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات (بياناتك الخاصة) ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
GEMINI_API_KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

# إعداد الذكاء الاصطناعي
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-pro')

# إعداد السجلات (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def get_ai_title():
    try:
        prompt = "اقترح عنواناً لقصة قصيرة مشوقة جداً (عنوان فقط بدون أي شرح أو مقدمات)"
        response = ai_model.generate_content(prompt)
        return response.text.strip()
    except:
        return "قصة غامضة من وراء الخيال"

async def get_ai_story(title):
    try:
        prompt = f"اكتب قصة قصيرة ومثيرة جداً بناءً على العنوان التالي: {title}. اجعل الأسلوب أدبي ممتع واستخدم ايموجي."
        response = ai_model.generate_content(prompt)
        return response.text
    except:
        return "عذراً، حدث خطأ أثناء تأليف القصة. حاول مجدداً."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = await get_ai_title()
    keyboard = [
        [InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
        [InlineKeyboardButton("🔄 لا، أريد قصة أخرى", callback_data="next")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✨ أهلاً بك في عالم القصص!\n\nهل تريد قصتك اليوم؟", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "next":
        title = await get_ai_title()
        keyboard = [
            [InlineKeyboardButton(f"📖 قراءة: {title}", callback_data=f"read|{title}")],
            [InlineKeyboardButton("🔄 قصة أخرى", callback_data="next")]
        ]
        await query.edit_message_text(f"ما رأيك بهذا العنوان؟\n\n🔹 **{title}**", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif query.data.startswith("read|"):
        title = query.data.split("|")[1]
        await query.edit_message_text(f"⏳ جاري تأليف قصة: **{title}**... انتظر قليلاً ✨")
        story_text = await get_ai_story(title)
        
        keyboard = [[InlineKeyboardButton("🔄 قصة جديدة", callback_data="next")]]
        await query.message.reply_text(f"📖 **{title}**\n\n{story_text}", 
                                       reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("البوت يعمل الآن بنجاح...")
    app.run_polling()
