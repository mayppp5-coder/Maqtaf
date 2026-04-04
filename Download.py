import logging
import os
import re
import random
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
    categories_keys = ["خيالية", "رعب", "دينية", "حقيقية", "تاريخية", "روايات", "رسالة"]
    for file in os.listdir():
        if file.endswith(".txt") and file != USERS_FILE:
            try:
                found_cat = next((k for k in categories_keys if k in file), None)
                if found_cat:
                    title = file.split("_", 1)[1].replace(".txt", "").strip() if "_" in file else file.replace(found_cat, "").replace(".txt", "").strip()
                    title = re.sub(r'^[^\w\u0621-\u064A]+', '', title).strip()
                    if found_cat not in library: library[found_cat] = {}
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if not content.strip(): continue
                        main_parts = content.split("NEXT_PART")
                        library[found_cat][title] = [[p.strip() for p in part.split("===") if p.strip()] for part in main_parts if part.strip()]
            except: pass
    return library

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    keyboard = [
        [InlineKeyboardButton("📚 قصص خيالية", callback_data="c_خيالية_0")],
        [InlineKeyboardButton("📚 قصص رعب", callback_data="c_رعب_0")],
        [InlineKeyboardButton("📚 قصص دينية", callback_data="c_دينية_0")],
        [InlineKeyboardButton("📚 قصص حقيقية", callback_data="c_حقيقية_0")],
        [InlineKeyboardButton("📚 قصص تاريخية", callback_data="c_تاريخية_0")],
        [InlineKeyboardButton("📚 روايات", callback_data="c_روايات_0")],
        [InlineKeyboardButton("✨ رسالة لك", callback_data="get_msg")],
        [InlineKeyboardButton("📩 اقتراح قصة", callback_data="suggest_story")] # الخانة الجديدة
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 لوحة التحكم", callback_data="admin")])
    
    msg = "🌟 **مرحباً بك في مكتبة القصص**\n\nاختر القسم الذي ترغب في تصفحه:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message: await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data, user_id = query.data, query.from_user.id
    await query.answer()
    all_data = get_stories_data()

    if data == "admin" and user_id == ADMIN_ID:
        users_count = len(get_users_list())
        await query.edit_message_text(f"📊 **لوحة التحكم**\n\n👥 عدد المشتركين الكلي: `{users_count}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

    # --- قسم الاقتراحات الجديد ---
    elif data == "suggest_story":
        msg = "💡 **لديك قصة رهيبة أو فكرة جديدة؟**\n\nيمكنك إرسال اقتراحك مباشرة للمطور عبر الزر أدناه:"
        # استبدال الرابط بـ tg://user?id=1077989275 ليفتح حسابك مباشرة
        keyboard = [
            [InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"tg://user?id={ADMIN_ID}")],
            [InlineKeyboardButton("🔙 عودة", callback_data="home")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "get_msg":
        if "رسالة" in all_data:
            all_msgs = []
            for t in all_data["رسالة"]:
                for part in all_data["رسالة"][t]:
                    all_msgs.extend(part)
            random_msg = random.choice(all_msgs)
            keyboard = [[InlineKeyboardButton("✨ رسالة أخرى", callback_data="get_msg")], [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")]]
            await query.edit_message_text(f"{random_msg}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("c_"):
        _, cat, page_num = data.split("_")
        page_num = int(page_num)
        if cat in all_data:
            titles = list(all_data[cat].keys())
            per_page = 5
            current_titles = titles[page_num*per_page : (page_num+1)*page_num+per_page]
            keyboard = [[InlineKeyboardButton(f"🔹 {t}", callback_data=f"l_{cat}_{titles.index(t)}")] for t in current_titles]
            nav = []
            if page_num > 0: nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"c_{cat}_{page_num-1}"))
            if (page_num+1)*per_page < len(titles): nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"c_{cat}_{page_num+1}"))
            if nav: keyboard.append(nav)
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("l_"):
        _, cat, t_idx = data.split("_", 2)
        titles = list(all_data[cat].keys())
        title = titles[int(t_idx)]
        parts = all_data[cat][title]
        if len(parts) == 1:
            keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data=f"c_{cat}_0")]]
            if len(parts[0]) > 1: keyboard.insert(0, [InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"r_{cat}_{t_idx}_0_1")])
            await query.edit_message_text(f"🔹 **{title}**\n\n{parts[0][0]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            keyboard = [[InlineKeyboardButton(f"✨ البارت {i+1}", callback_data=f"r_{cat}_{t_idx}_{i}_0")] for i in range(len(parts))]
            keyboard.append([InlineKeyboardButton("🔙 عودة", callback_data=f"c_{cat}_0")])
            await query.edit_message_text(f"✨ **{title}**\nاختر الجزء:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("r_"):
        _, cat, t_idx, p_idx, s_idx = data.split("_", 4)
        t_idx, p_idx, s_idx = int(t_idx), int(p_idx), int(s_idx)
        titles = list(all_data[cat].keys())
        title = titles[t_idx]
        pages = all_data[cat][title][p_idx]
        keyboard = []
        if s_idx + 1 < len(pages): keyboard.append([InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"r_{cat}_{t_idx}_{p_idx}_{s_idx+1}")])
        elif p_idx + 1 < len(all_data[cat][title]): keyboard.append([InlineKeyboardButton("البارت التالي ⏭", callback_data=f"r_{cat}_{t_idx}_{p_idx+1}_0")])
        keyboard.append([InlineKeyboardButton("🔙 قائمة البارتات", callback_data=f"l_{cat}_{t_idx}")])
        await query.edit_message_text(f"✨ **{title}**\n\n{pages[s_idx]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "home": await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
