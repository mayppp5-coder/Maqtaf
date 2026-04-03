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
                        content = f.read()
                        if not content.strip(): continue
                        # التقسيم باستخدام === للأجزاء
                        parts = [p.strip() for p in content.split("===") if p.strip()]
                        library[found_cat][title] = parts
            except: pass
    return library

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    keyboard = [
        [InlineKeyboardButton("📚 قصص خيالية", callback_data="c_خيالية")],
        [InlineKeyboardButton("📚 قصص رعب", callback_data="c_رعب")],
        [InlineKeyboardButton("📚 قصص دينية", callback_data="c_دينية")],
        [InlineKeyboardButton("📚 قصص حقيقية", callback_data="c_حقيقية")],
        [InlineKeyboardButton("📚 قصص تاريخية", callback_data="c_تاريخية")],
        [InlineKeyboardButton("📚 روايات", callback_data="c_روايات")],
        [InlineKeyboardButton("💡 نصيحة اليوم", callback_data="direct_advice")]
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
        await query.edit_message_text(f"📊 **لوحة التحكم**\n\n👥 عدد المشتركين: `{users_count}`", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

    elif data == "direct_advice":
        if "نصيحة" in all_data:
            all_advices = []
            for t in all_data["نصيحة"]: all_advices.extend(all_data["نصيحة"][t])
            random_advice = random.choice(all_advices)
            await query.edit_message_text(f"{random_advice}", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 نصيحة أخرى", callback_data="direct_advice")], [InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

    elif data.startswith("c_"):
        cat = data.split("_")[1]
        if cat in all_data:
            titles = list(all_data[cat].keys())
            # نرسل الـ Index 0 كبداية للجزء الأول
            keyboard = [[InlineKeyboardButton(f"🔹 {t}", callback_data=f"l_{cat}_{titles.index(t)}_0")] for t in titles]
            keyboard.append([InlineKeyboardButton("🔙 عودة", callback_data="home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("l_"):
        parts_data = data.split("_")
        cat = parts_data[1]
        t_idx = int(parts_data[2])
        p_idx = int(parts_data[3]) # رقم الجزء الحالي
        
        titles = list(all_data[cat].keys())
        title = titles[t_idx]
        all_parts = all_data[cat][title]
        content = all_parts[p_idx]
        
        keyboard = []
        # إذا كان هناك جزء تالي، أضف زر التكملة
        if p_idx + 1 < len(all_parts):
            keyboard.append([InlineKeyboardButton("✨ تكملة القصة", callback_data=f"l_{cat}_{t_idx}_{p_idx+1}")])
        
        # أزرار التنقل والعودة
        nav_buttons = []
        if p_idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"l_{cat}_{t_idx}_{p_idx-1}"))
        nav_buttons.append(InlineKeyboardButton("🔙 عودة للقسم", callback_data=f"c_{cat}"))
        keyboard.append(nav_buttons)
        
        await query.edit_message_text(f"🔹 **{title}** (جزء {p_idx+1})\n\n{content}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "home": await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
