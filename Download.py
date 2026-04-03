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

# --- إدارة المستخدمين ---
def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{str(user_id)}\n")

def get_users_list():
    if not os.path.exists(USERS_FILE): return []
    with open(USERS_FILE, "r") as f:
        return f.read().splitlines()

# --- جلب البيانات ---
def get_stories_data():
    library = {}
    categories_keys = ["خيالية", "رعب", "دينية", "حقيقية", "تاريخية", "روايات", "نصيحة"]
    for file in os.listdir():
        if file.endswith(".txt") and file != USERS_FILE:
            try:
                found_cat = next((k for k in categories_keys if k in file), None)
                if found_cat:
                    title = file.split("_", 1)[1].replace(".txt", "").strip() if "_" in file else file.replace(found_cat, "").replace(".txt", "").strip()
                    title = re.sub(r'^[^\w\u0621-\u064A]+', '', title).strip()
                    if found_cat not in library: library[found_cat] = {}
                    with open(file, 'r', encoding='utf-8') as f:
                        main_parts = f.read().split("NEXT_PART")
                        library[found_cat][title] = [[p.strip() for p in part.split("===") if p.strip()] for part in main_parts if part.strip()]
            except: pass
    return library

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    keyboard = [
        [InlineKeyboardButton("📚 قصص خيالية", callback_data="maincat_خيالية_0")],
        [InlineKeyboardButton("📚 قصص رعب", callback_data="maincat_رعب_0")],
        [InlineKeyboardButton("📚 قصص دينية", callback_data="maincat_دينية_0")],
        [InlineKeyboardButton("📚 قصص حقيقية", callback_data="maincat_حقيقية_0")],
        [InlineKeyboardButton("📚 قصص تاريخية", callback_data="maincat_تاريخية_0")],
        [InlineKeyboardButton("📚 روايات", callback_data="maincat_روايات_0")],
        [InlineKeyboardButton("💡 نصيحة اليوم", callback_data="maincat_نصيحة_0")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 لوحة التحكم", callback_data="admin_panel")])
    
    msg = "🌟 **مرحباً بك في مكتبة القصص**\n\nاختر القسم الذي ترغب في تصفحه:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message: await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data, user_id = query.data, query.from_user.id
    await query.answer()
    all_data = get_stories_data()

    # --- كود لوحة التحكم ---
    if data == "admin_panel" and user_id == ADMIN_ID:
        users_count = len(get_users_list())
        keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="back_home")]]
        await query.edit_message_text(f"📊 **لوحة التحكم (المسؤول)**\n\n👥 عدد المشتركين الكلي: `{users_count}`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("maincat_"):
        _, cat, page_num = data.split("_")
        page_num = int(page_num)
        if cat in all_data:
            titles = list(all_data[cat].keys())
            per_page = 5
            current_titles = titles[page_num*per_page : (page_num+1)*per_page]
            keyboard = [[InlineKeyboardButton(f"✨ {t}", callback_data=f"listparts_{cat}_{t}")] for t in current_titles]
            nav = []
            if page_num > 0: nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"maincat_{cat}_{page_num-1}"))
            if (page_num+1)*per_page < len(titles): nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"maincat_{cat}_{page_num+1}"))
            if nav: keyboard.append(nav)
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text(f"⚠️ قسم **{cat}** فارغ حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back_home")]]))

    elif data.startswith("listparts_"):
        _, cat, title = data.split("_", 2)
        parts = all_data[cat][title]
        if len(parts) == 1:
            keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data=f"maincat_{cat}_0")]]
            if len(parts[0]) > 1: keyboard.insert(0, [InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"read_{cat}_{title}_0_1")])
            await query.edit_message_text(f"✨ **{title}**\n\n{parts[0][0]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            keyboard = [[InlineKeyboardButton(f"✨ البارت {i+1}", callback_data=f"read_{cat}_{title}_{i}_0")] for i in range(len(parts))]
            keyboard.append([InlineKeyboardButton("🔙 عودة", callback_data=f"maincat_{cat}_0")])
            await query.edit_message_text(f"✨ **{title}**\nاختر الجزء:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("read_"):
        _, cat, title, p_idx, s_idx = data.split("_", 4)
        p_idx, s_idx = int(p_idx), int(s_idx)
        pages = all_data[cat][title][p_idx]
        keyboard = []
        if s_idx + 1 < len(pages): keyboard.append([InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"read_{cat}_{title}_{p_idx}_{s_idx+1}")])
        elif p_idx + 1 < len(all_data[cat][title]): keyboard.append([InlineKeyboardButton("البارت التالي ⏭", callback_data=f"read_{cat}_{title}_{p_idx+1}_0")])
        keyboard.append([InlineKeyboardButton("🔙 قائمة البارتات", callback_data=f"listparts_{cat}_{title}")])
        await query.edit_message_text(f"✨ **{title}**\n\n{pages[s_idx]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "back_home": await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
