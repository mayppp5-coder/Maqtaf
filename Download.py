import logging
import os
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
ADMIN_ID = 1077989275 
USERS_FILE = "users.txt"

logging.basicConfig(level=logging.INFO)

# --- وظيفة جلب البيانات - النسخة النهائية الفائقة ---
def get_stories_data():
    library = {}
    # كلمات البحث الأساسية (أضفنا احتمالات الياء والألف المقصورة لضمان الدقة)
    categories_keys = {
        "خيالية": ["خيالية", "خياليه"],
        "رعب": ["رعب"],
        "دينية": ["دينية", "دينيه"],
        "حقيقية": ["حقيقية", "حقيقيه"],
        "تاريخية": ["تاريخية", "تاريخيه"],
        "روايات": ["روايات", "رواية", "روايه"],
        "نصيحة": ["نصيحة", "نصيحه"]
    }
    
    for file in os.listdir():
        if file.endswith(".txt") and file != USERS_FILE:
            try:
                found_cat_key = None
                # بحث مرن عن القسم
                for main_key, variations in categories_keys.items():
                    if any(v in file for v in variations):
                        found_cat_key = main_key
                        break
                
                if found_cat_key:
                    # تنظيف اسم الملف لاستخراج العنوان
                    # حذف النقاط والرموز من البداية والنهاية
                    clean_filename = file.replace(".txt", "")
                    if "_" in clean_filename:
                        title = clean_filename.split("_", 1)[1].strip()
                    else:
                        title = clean_filename.replace(found_cat_key, "").strip()
                    
                    # مسح أي رموز تبقت في العنوان (مثل النقاط)
                    title = re.sub(r'^[^\w\u0621-\u064A]+', '', title).strip()
                    
                    if found_cat_key not in library: library[found_cat_key] = {}
                    
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        main_parts = content.split("NEXT_PART")
                        parsed_parts = [[page.strip() for page in p.split("===") if page.strip()] for p in main_parts if p.strip()]
                        library[found_cat_key][title] = parsed_parts
                        logging.info(f"✅ تم تحميل: {title} في قسم {found_cat_key}")
            except Exception as e:
                logging.error(f"❌ خطأ في ملف {file}: {e}")
    return library

# --- الأوامر الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("✨ قصص خيالية", callback_data="maincat_خيالية_0")],
        [InlineKeyboardButton("✨ قصص رعب", callback_data="maincat_رعب_0")],
        [InlineKeyboardButton("✨ قصص دينية", callback_data="maincat_دينية_0")],
        [InlineKeyboardButton("✨ قصص حقيقية", callback_data="maincat_حقيقية_0")],
        [InlineKeyboardButton("✨ قصص تاريخية", callback_data="maincat_تاريخية_0")],
        [InlineKeyboardButton("✨ روايات", callback_data="maincat_روايات_0")],
        [InlineKeyboardButton("💡 نصيحة اليوم", callback_data="maincat_نصيحة_0")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 لوحة التحكم", callback_data="admin_panel")])
        
    msg = "🌟 **مرحباً بك في مكتبة القصص**\n\nاختر القسم الذي ترغب في تصفحه:"
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- معالجة الأزرار ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    all_data = get_stories_data()

    if data.startswith("maincat_"):
        parts = data.split("_")
        cat = parts[1]
        page_num = int(parts[2]) if len(parts) > 2 else 0
        
        if cat in all_data:
            titles = list(all_data[cat].keys())
            per_page = 5
            start_idx = page_num * per_page
            current_titles = titles[start_idx : start_idx + per_page]
            keyboard = [[InlineKeyboardButton(f"✨ {t}", callback_data=f"listparts_{cat}_{t}")] for t in current_titles]
            nav_buttons = []
            if page_num > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"maincat_{cat}_{page_num-1}"))
            if start_idx + per_page < len(titles):
                nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"maincat_{cat}_{page_num+1}"))
            if nav_buttons: keyboard.append(nav_buttons)
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text(f"⚠️ قسم **{cat}** لا يحتوي على ملفات حالياً.\nتأكد من تسمية الملف بـ (تاريخية_اسم القصة).", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back_home")]]))

    elif data.startswith("listparts_"):
        _, cat, title = data.split("_", 2)
        parts = all_data[cat][title]
        if len(parts) == 1:
            keyboard = [[InlineKeyboardButton("🔙 عودة للقسم", callback_data=f"maincat_{cat}_0")]]
            if len(parts[0]) > 1:
                keyboard.insert(0, [InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"read_{cat}_{title}_0_1")])
            await query.edit_message_text(f"✨ **{title}**\n\n{parts[0][0]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            keyboard = [[InlineKeyboardButton(f"✨ البارت {i+1}", callback_data=f"read_{cat}_{title}_{i}_0")] for i in range(len(parts))]
            keyboard.append([InlineKeyboardButton("🔙 عودة للقسم", callback_data=f"maincat_{cat}_0")])
            await query.edit_message_text(f"✨ رواية: **{title}**\nاختر البارت:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("read_"):
        _, cat, title, p_idx, s_idx = data.split("_", 4)
        p_idx, s_idx = int(p_idx), int(s_idx)
        pages = all_data[cat][title][p_idx]
        keyboard = []
        if s_idx + 1 < len(pages):
            keyboard.append([InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"read_{cat}_{title}_{p_idx}_{s_idx+1}")])
        elif p_idx + 1 < len(all_data[cat][title]):
            keyboard.append([InlineKeyboardButton("البارت التالي ⏭", callback_data=f"read_{cat}_{title}_{p_idx+1}_0")])
        keyboard.append([InlineKeyboardButton("🔙 قائمة البارتات", callback_data=f"listparts_{cat}_{title}")])
        await query.edit_message_text(f"✨ **{title} - البارت {p_idx+1}**\n\n{pages[s_idx]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "back_home":
        await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
