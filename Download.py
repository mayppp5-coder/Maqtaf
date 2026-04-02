import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# توكن البوت الخاص بك
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"

logging.basicConfig(level=logging.INFO)

def get_stories_data():
    library = {}
    for file in os.listdir():
        if file.endswith(".txt") and "_" in file:
            try:
                category, title = file.replace(".txt", "").split("_", 1)
                if category not in library:
                    library[category] = {}
                
                with open(file, 'r', encoding='utf-8') as f:
                    parts = f.read().split("===")
                    library[category][title.replace("_", " ")] = [p.strip() for p in parts if p.strip()]
            except:
                continue
    return library

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الترتيب الذي طلبته بالضبط
    keyboard = [
        [InlineKeyboardButton("🧚‍♂️ قصص خيالية", callback_data="maincat_خيالية"), InlineKeyboardButton("👻 قصص رعب", callback_data="maincat_رعب")],
        [InlineKeyboardButton("📚 روايات", callback_data="maincat_روايات"), InlineKeyboardButton("⚔️ قصص الحروب", callback_data="maincat_الحروب")],
        [InlineKeyboardButton("✨ قصص الأنبياء", callback_data="maincat_الأنبياء"), InlineKeyboardButton("🕌 قصص إسلامية", callback_data="maincat_إسلامية")],
        [InlineKeyboardButton("✅ قصص حقيقية", callback_data="maincat_حقيقية"), InlineKeyboardButton("🇮🇶 قصص عراقية", callback_data="maincat_عراقية")],
        [InlineKeyboardButton("⚔️ قصص الامام علي", callback_data="maincat_الامام_علي"), InlineKeyboardButton("🏛️ أساطير تاريخية", callback_data="maincat_أساطير")],
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

    if data.startswith("maincat_"):
        cat = data.replace("maincat_", "")
        if cat in all_data:
            keyboard = []
            for title in all_data[cat].keys():
                icon = "💡" if cat == "نصيحة" else "📖"
                keyboard.append([InlineKeyboardButton(f"{icon} {title}", callback_data=f"view_{cat}_{title}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_home")])
            title_msg = "💡 نصائح اليوم:" if cat == "نصيحة" else f"📍 قسم: {cat}"
            await query.edit_message_text(title_msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer("جاري إضافة المحتوى لهذا القسم.. ⏳", show_alert=True)

    elif data.startswith("view_"):
        _, cat, title = data.split("_", 2)
        idx = 0
        text = all_data[cat][title][idx]
        keyboard = []
        
        # إذا كانت هناك تكملة (باستخدام ===)
        if len(all_data[cat][title]) > 1:
            keyboard.append([InlineKeyboardButton("التكملة ⬇️", callback_data=f"nxt_{cat}_{title}_{idx+1}")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة للقسم", callback_data=f"maincat_{cat}")])
        
        display_text = f"💡 **نصيحة اليوم: {title}**\n\n{text}" if cat == "نصيحة" else text
        await query.edit_message_text(display_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "back_home":
        await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
