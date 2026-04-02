import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# توكن البوت الخاص بك
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"

logging.basicConfig(level=logging.INFO)

# دالة لجلب البيانات وتقسيمها من ملفات الـ txt المرفوعة على GitHub
def get_stories_data():
    library = {}
    for file in os.listdir():
        if file.endswith(".txt") and "_" in file:
            try:
                # تقسيم اسم الملف: (القسم_اسم القصة.txt)
                category, title = file.replace(".txt", "").split("_", 1)
                if category not in library:
                    library[category] = {}
                with open(file, 'r', encoding='utf-8') as f:
                    # تقسيم المحتوى بناءً على الرمز ===
                    parts = f.read().split("===")
                    library[category][title.replace("_", " ")] = [p.strip() for p in parts if p.strip()]
            except:
                continue
    return library

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الأزرار مرتبة بالطول مع إيموجي الكتاب 📚
    keyboard = [
        [InlineKeyboardButton("📚 قصص خيالية", callback_data="maincat_خيالية")],
        [InlineKeyboardButton("📚 قصص رعب", callback_data="maincat_رعب")],
        [InlineKeyboardButton("📚 روايات", callback_data="maincat_روايات")],
        [InlineKeyboardButton("📚 قصص الحروب", callback_data="maincat_الحروب")],
        [InlineKeyboardButton("📚 قصص الأنبياء", callback_data="maincat_الأنبياء")],
        [InlineKeyboardButton("📚 قصص إسلامية", callback_data="maincat_إسلامية")],
        [InlineKeyboardButton("📚 قصص حقيقية", callback_data="maincat_حقيقية")],
        [InlineKeyboardButton("📚 قصص عراقية", callback_data="maincat_عراقية")],
        [InlineKeyboardButton("📚 قصص الامام علي", callback_data="maincat_الامام_علي")],
        [InlineKeyboardButton("📚 قصص أساطير تاريخية", callback_data="maincat_أساطير")],
        [InlineKeyboardButton("💡 نصيحتي لك اليوم", callback_data="maincat_نصيحة")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "🌟 **مرحباً بك في مكتبة القصص والنصائح**\n\nاختر القسم الذي ترغب في تصفحه:"
    
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    all_data = get_stories_data()

    # الدخول للقسم وعرض قائمة القصص التابعة له
    if data.startswith("maincat_"):
        cat = data.replace("maincat_", "")
        if cat in all_data:
            keyboard = []
            for title in all_data[cat].keys():
                icon = "💡" if cat == "نصيحة" else "📖"
                keyboard.append([InlineKeyboardButton(f"{icon} {title}", callback_data=f"view_{cat}_{title}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_home")])
            title_msg = "💡 قائمة النصائح:" if cat == "نصيحة" else f"📍 قسم: {cat.replace('_', ' ')}"
            await query.edit_message_text(title_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer("جاري إضافة المحتوى لهذا القسم.. قريباً! ⏳", show_alert=True)

    # عرض محتوى القصة (البارت الأول)
    elif data.startswith("view_"):
        _, cat, title = data.split("_", 2)
        idx = 0
        text = all_data[cat][title][idx]
        keyboard = []
        if len(all_data[cat][title]) > 1:
            keyboard.append([InlineKeyboardButton("التكملة ⬇️", callback_data=f"nxt_{cat}_{title}_{idx+1}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة للقسم", callback_data=f"maincat_{cat}")])
        
        display_text = f"💡 **{title}**\n\n{text}" if cat == "نصيحة" else f"📖 **{title}**\n\n{text}"
        await query.edit_message_text(display_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # التنقل بين أجزاء القصة (التكملة)
    elif data.startswith("nxt_"):
        _, cat, title, idx = data.split("_", 3)
        idx = int(idx)
        text = all_data[cat][title][idx]
        keyboard = []
        if idx + 1 < len(all_data[cat][title]):
            keyboard.append([InlineKeyboardButton("التكملة ⬇️", callback_data=f"nxt_{cat}_{title}_{idx+1}")])
        else:
            label = "🔙 عودة للنصائح" if cat == "نصيحة" else "🏁 نهاية القصة"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"maincat_{cat}")])
        
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "back_home":
        await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
