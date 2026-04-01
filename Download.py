import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from stories import stories_library, tips_library

TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for category in stories_library.keys():
        keyboard.append([InlineKeyboardButton(f"📚 {category}", callback_data=f"cat_{category}")])
    
    # إضافة زر النصيحة في القائمة الرئيسية
    keyboard.append([InlineKeyboardButton("💡 نصيحتي لك اليوم", callback_data="daily_tip")])
    
    await update.message.reply_text("✨ مرحباً بك! اختر القسم الذي تفضله:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("cat_"):
        cat = data.replace("cat_", "")
        story = random.choice(stories_library[cat])
        keyboard = [
            [InlineKeyboardButton("📖 الجزء الثاني", callback_data="coming_soon")],
            [InlineKeyboardButton(f"🔄 قصة {cat} أخرى", callback_data=f"cat_{cat}")],
            [InlineKeyboardButton("🔙 الرجوع للأقسام", callback_data="main")]
        ]
        await query.message.reply_text(story, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "coming_soon":
        # إظهار رسالة تنبيهية (Popup) للمستخدم
        await query.answer("انتظرونا.. الجزء الثاني قريباً جداً! 🔥", show_alert=True)

    elif data == "daily_tip":
        tip = random.choice(tips_library)
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main")]]
        await query.message.reply_text(f"💡 **نصيحتي لك اليوم:**\n\n{tip}", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), 
                                      parse_mode="Markdown")
        await query.answer()

    elif data == "main":
        keyboard = [[InlineKeyboardButton(f"📚 {c}", callback_data=f"cat_{c}")] for c in stories_library.keys()]
        keyboard.append([InlineKeyboardButton("💡 نصيحتي لك اليوم", callback_data="daily_tip")])
        await query.edit_message_text("اختر القسم الذي تفضله:", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling(drop_pending_updates=True)
