import logging
import os
import re
import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --- الإعدادات الأساسية ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
ADMIN_ID = 1077989275 
CHANNEL_ID = "@Aqarani_" 
CHANNEL_URL = "https://t.me/Aqarani_"

# الحفظ في المجلد الرئيسي مباشرة (لأن الـ Volume غير متاح عندك)
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

# --- جلب البيانات (تلقائياً من ملفاتك) ---
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

# --- التحقق من الاشتراك الإجباري ---
async def check_subscription(user_id, context):
    if user_id == ADMIN_ID: return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return True 

# --- القائمة الرئيسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        msg = ("✨ أهلاً بك في بوت أقـراني\n\n"
               "حتى تقدر تستمتع بكل القصص والمحتوى، فقط اشترك بالقناة\n"
               "وبعدها اضغط على “تحقق” وراح يفتح لك البوت بالكامل 🤍")
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_URL)], [InlineKeyboardButton("✅ تحقق", callback_data="check_sub")]]
        if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else: await update.callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    save_user(user_id)
    keyboard = [
        [InlineKeyboardButton("📚 خيالية", callback_data="c_خيالية_0"), InlineKeyboardButton("📚 رعب", callback_data="c_رعب_0")],
        [InlineKeyboardButton("📚 دينية", callback_data="c_دينية_0"), InlineKeyboardButton("📚 حقيقية", callback_data="c_حقيقية_0")],
        [InlineKeyboardButton("📚 تاريخية", callback_data="c_تاريخية_0"), InlineKeyboardButton("📚 روايات", callback_data="c_روايات_0")],
        [InlineKeyboardButton("✨ رسالة لك", callback_data="get_msg")],
        [InlineKeyboardButton("📩 اقتراح قصة", callback_data="suggest_story")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    
    msg = "🌟 **مرحباً بك في مكتبة القصص**\n\nاختر القسم الذي ترغب في تصفحه:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message: await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

# --- معالجة الأزرار ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data, user_id = query.data, query.from_user.id
    await query.answer()
    all_data = get_stories_data()

    if data == "check_sub":
        if await check_subscription(user_id, context): await start(update, context)
        else: await query.answer("❌ أنت غير مشترك في القناة بعد!", show_alert=True)
        return

    if data == "admin_panel" and user_id == ADMIN_ID:
        count = len(get_users_list())
        msg = f"⚙️ **لوحة التحكم**\n\n👥 عدد المشتركين: `{count}`"
        keyboard = [[InlineKeyboardButton("📣 إذاعة للجميع", callback_data="broadcast")], [InlineKeyboardButton("🔙 عودة", callback_data="home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "broadcast" and user_id == ADMIN_ID:
        context.user_data['waiting_broadcast'] = True
        await query.edit_message_text("✍️ أرسل رسالة الإذاعة الآن:")

    elif data == "suggest_story":
        await query.edit_message_text("تواصل مع المطور:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 مقتدى", url=f"tg://user?id={ADMIN_ID}")], [InlineKeyboardButton("🔙", callback_data="home")]]))

    elif data == "get_msg":
        if "رسالة" in all_data:
            all_msgs = [m for t in all_data["رسالة"] for p in all_data["رسالة"][t] for m in p]
            await query.edit_message_text(f"{random.choice(all_msgs)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✨ رسالة أخرى", callback_data="get_msg")], [InlineKeyboardButton("🔙", callback_data="home")]]))

    elif data.startswith("c_"):
        _, cat, p_num = data.split("_")
        p_num = int(p_num)
        if cat in all_data:
            titles = list(all_data[cat].keys())
            curr = titles[p_num*5 : (p_num+1)*5]
            keyboard = [[InlineKeyboardButton(t, callback_data=f"l_{cat}_{titles.index(t)}")] for t in curr]
            nav = []
            if p_num > 0: nav.append(InlineKeyboardButton("⬅️", callback_data=f"c_{cat}_{p_num-1}"))
            if (p_num+1)*5 < len(titles): nav.append(InlineKeyboardButton("➡️", callback_data=f"c_{cat}_{p_num+1}"))
            if nav: keyboard.append(nav)
            keyboard.append([InlineKeyboardButton("🔙 عودة", callback_data="home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("l_"):
        _, cat, t_idx = data.split("_", 2)
        title = list(all_data[cat].keys())[int(t_idx)]
        parts = all_data[cat][title]
        if len(parts) == 1:
            kb = [[InlineKeyboardButton("🔙 عودة", callback_data=f"c_{cat}_0")]]
            if len(parts[0]) > 1: kb.insert(0, [InlineKeyboardButton("تكملة ⬇️", callback_data=f"r_{cat}_{t_idx}_0_1")])
            await query.edit_message_text(f"🔹 **{title}**\n\n{parts[0][0]}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            kb = [[InlineKeyboardButton(f"✨ البارت {i+1}", callback_data=f"r_{cat}_{t_idx}_{i}_0")] for i in range(len(parts))]
            kb.append([InlineKeyboardButton("🔙", callback_data=f"c_{cat}_0")])
            await query.edit_message_text(f"✨ **{title}**", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("r_"):
        _, cat, t_idx, p_idx, s_idx = data.split("_", 4)
        t_idx, p_idx, s_idx = int(t_idx), int(p_idx), int(s_idx)
        title = list(all_data[cat].keys())[t_idx]
        pages = all_data[cat][title][p_idx]
        kb = []
        if s_idx+1 < len(pages): kb.append([InlineKeyboardButton("تكملة ⬇️", callback_data=f"r_{cat}_{t_idx}_{p_idx}_{s_idx+1}")])
        elif p_idx+1 < len(all_data[cat][title]): kb.append([InlineKeyboardButton("البارت التالي ⏭", callback_data=f"r_{cat}_{t_idx}_{p_idx+1}_0")])
        kb.append([InlineKeyboardButton("🔙 قائمة البارتات", callback_data=f"l_{cat}_{t_idx}")])
        await query.edit_message_text(f"✨ **{title}**\n\n{pages[s_idx]}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "home": await start(update, context)

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and context.user_data.get('waiting_broadcast'):
        context.user_data['waiting_broadcast'] = False
        users = get_users_list()
        for u in users:
            try: await context.bot.send_message(chat_id=u, text=f"📢 **رسالة من الإدارة:**\n\n{update.message.text}")
            except: pass
        await update.message.reply_text("✅ تم إرسال الإذاعة.")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_handler))
    app.run_polling()
