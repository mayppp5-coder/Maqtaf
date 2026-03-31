import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# استيراد مكتبة القصص المصنفة
try:
    from stories import stories_library
except ImportError:
    stories_library = {}

TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # إنشاء أزرار للأصناف
    keyboard = []
    # نأخذ أسماء الأصناف من القاموس ونحولها لأزرار
    for category in stories_library.keys():
        keyboard.append([InlineKeyboardButton(f"📚 قصص {category}", callback_data=f"cat_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✨ مرحباً بك في عالم القصص!\nاختر القسم الذي تفضله:", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("cat_"):
        # استخراج اسم الصنف من بيانات الزر
        category_name = query.data.replace("cat_", "")
        
        if category_name in stories_library:
            # اختيار قصة عشوائية من الصنف المحدد
            selected_story = random.choice(stories_library[category_name])
            
            # زر للعودة للقائمة الرئيسية وزر لقصة أخرى من نفس النوع
            keyboard = [
                [InlineKeyboardButton(f"🔄 قصة {category_name} أخرى", callback_data=f"cat_{category_name}")],
                [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
            ]
            
            await query.message.reply_text(selected_story, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "main_menu":
        # إعادة عرض القائمة الرئيسية
        keyboard = []
        for category in stories_library.keys():
            keyboard.append([InlineKeyboardButton(f"📚 قصص {category}", callback_data=f"cat_{category}")])
        
        await query.edit_message_text("اختر القسم الذي تفضله:", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling(drop_pending_updates=True)
