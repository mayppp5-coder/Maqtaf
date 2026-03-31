import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
# استيراد القصص من الملف الجديد
try:
    from stories import stories_library
except ImportError:
    stories_library = ["⚠️ ملف القصص غير موجود، يرجى التأكد من رفعه."]

TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎲 قراءة قصة عشوائية", callback_data="get_story")]]
    await update.message.reply_text(
        "✨ مرحباً بك في أكبر مكتبة قصص!\n\nلدينا أكثر من 200 قصة بانتظارك.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_story":
        selected_story = random.choice(stories_library)
        keyboard = [[InlineKeyboardButton("🔄 قصة أخرى", callback_data="get_story")]]
        
        # نستخدم رسالة جديدة لتجنب التكرار
        await query.message.reply_text(selected_story, reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling(drop_pending_updates=True)
