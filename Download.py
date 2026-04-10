import logging
import os
import re
import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest

# --- الإعدادات الأساسية ---
TELEGRAM_TOKEN = "8616870028:AAET1lFcvbeU_BJ0ARsirgI9_5Fggxt7nsE"
ADMIN_ID = 1077989275 
CHANNEL_ID = "@Aqarani" 
CHANNEL_URL = "https://t.me/Aqarani"
USERS_FILE = "users.txt" 

logging.basicConfig(level=logging.INFO)

# --- نظام إدارة المشتركين ---
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

# --- جلب القصص وتنسيقها ---
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
                        # تقسيم القصة بناءً على NEXT_PART
                        main_parts = content.split("NEXT_PART")
                        # كل جزء (Part) يتم تقسيمه لصفحات (Pages) بناءً على ===
                        library[found_cat][title] = [[p.strip() for p in part.split("===") if p.strip()] for part in main_parts if part.strip()]
            except: pass
    return library

# --- التحقق من الاشتراك الإجباري ---
async def check_subscription(user_id, context):
    if user_id == ADMIN_ID: return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

# --- القائمة الرئيسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        msg = ("🌿 مرحباً بك في بوت أقـراني\n\n"
               "حتى نكمل معك الحكاية، اشترك بالقناة أولاً ✨\n\n"
               "وبعدها اضغط “تحقق” لنفتح لك كل شيء بكل حب 🤍")
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_URL)], [InlineKeyboardButton("✅ تحقق", callback_data="check_sub")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message: await update.message.reply_text(msg, reply_markup=reply_markup)
        else: await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)
        return

    save_user(user_id)
    keyboard = [
        [InlineKeyboardButton("رعب 📚", callback_data="c_رعب_0"), InlineKeyboardButton("خيالية 📚", callback_data="c_خيالية_0")],
        [InlineKeyboardButton("حقيقية 📚", callback_data="c_حقيقية_0"), InlineKeyboardButton("دينية 📚", callback_data="c_دينية_0")],
        [InlineKeyboardButton("روايات 📚", callback_data="c_روايات_0"), InlineKeyboardButton("تاريخية 📚", callback_data="c_تاريخية_0")],
        [InlineKeyboardButton("رسالة لك ✨", callback_data="get_msg")],
        [InlineKeyboardButton("📩 اقتراح قصة", callback_data="suggest")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    
    msg = "🌟 **مرحباً بك في مكتبة القصص**\n\nاختر القسم الذي ترغب في تصفحه:"
    if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- معالجة الأزرار ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data, user_id = query.data, query.from_user.id
    all_data = get_stories_data()

    if data == "check_sub":
        if await check_subscription(user_id, context):
            await query.answer("✅ تم التحقق!")
            await start(update, context)
        else: await query.answer("❌ اشترك أولاً!", show_alert=True)
        return

    await query.answer()

    if data == "home": await start(update, context)

    elif data == "admin_panel" and user_id == ADMIN_ID:
        count = len(get_users_list())
        msg = f"⚙️ **لوحة التحكم**\n\n👥 عدد المشتركين: `{count}`"
        keyboard = [[InlineKeyboardButton("📣 إذاعة", callback_data="broadcast"), InlineKeyboardButton("📥 نسخة احتياطية", callback_data="backup")], [InlineKeyboardButton("🔙 عودة", callback_data="home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "suggest":
        await query.edit_message_text("لإرسال اقتراحاتك، تواصل مع المطور:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={ADMIN_ID}")], [InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

    elif data.startswith("c_"):
        _, cat, p_num = data.split("_")
        p_num = int(p_num)
        if cat in all_data:
            titles = list(all_data[cat].keys())
            curr = titles[p_num*8 : (p_num+1)*8]
            keyboard = [[InlineKeyboardButton(f"📖 {t}", callback_data=f"l_{cat}_{titles.index(t)}")] for t in curr]
            nav = []
            if p_num > 0: nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"c_{cat}_{p_num-1}"))
            if (p_num+1)*8 < len(titles): nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"c_{cat}_{p_num+1}"))
            if nav: keyboard.append(nav)
            keyboard.append([InlineKeyboardButton("🔙 عودة", callback_data="home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("l_"):
        _, cat, t_idx = data.split("_", 2)
        t_idx = int(t_idx)
        title = list(all_data[cat].keys())[t_idx]
        parts = all_data[cat][title]
        
        # التعديل هنا: إذا كانت القصة جزءاً واحداً فقط، تفتح مباشرة
        if len(parts) == 1:
            await query.edit_message_text(f"✨ **{title}**\n\n{parts[0][0]}", 
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("التكملة ⬇️", callback_data=f"r_{cat}_{t_idx}_0_1")] if len(parts[0]) > 1 else [],
                    [InlineKeyboardButton("🔙 القائمة", callback_data=f"c_{cat}_0")]
                ]), parse_mode="Markdown")
        else:
            # إذا كانت أكثر من جزء (بسبب وجود NEXT_PART)
            kb = [[InlineKeyboardButton(f"✨ البارت {i+1}", callback_data=f"r_{cat}_{t_idx}_{i}_0")] for i in range(len(parts))]
            kb.append([InlineKeyboardButton("🔙 عودة", callback_data=f"c_{cat}_0")])
            await query.edit_message_text(f"📖 **{title}**\nاختر البارت:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("r_"):
        _, cat, t_idx, p_idx, s_idx = data.split("_", 4)
        t_idx, p_idx, s_idx = int(t_idx), int(p_idx), int(s_idx)
        title = list(all_data[cat].keys())[t_idx]
        pages = all_data[cat][title][p_idx]
        kb = []
        if s_idx+1 < len(pages): kb.append([InlineKeyboardButton("التكملة ⬇️", callback_data=f"r_{cat}_{t_idx}_{p_idx}_{s_idx+1}")])
        elif p_idx+1 < len(all_data[cat][title]): kb.append([InlineKeyboardButton("البارت التالي ⏭", callback_data=f"r_{cat}_{t_idx}_{p_idx+1}_0")])
        
        # الرجوع للقائمة الرئيسية للقسم إذا كانت جزءاً واحداً، أو قائمة البارتات إذا كانت متعددة
        back_data = f"c_{cat}_0" if len(all_data[cat][title]) == 1 else f"l_{cat}_{t_idx}"
        kb.append([InlineKeyboardButton("🔙 القائمة", callback_data=back_data)])
        
        await query.edit_message_text(f"✨ **{title}**\n\n{pages[s_idx]}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and context.user_data.get('waiting_broadcast'):
        context.user_data['waiting_broadcast'] = False
        for u in get_users_list():
            try: await context.bot.send_message(chat_id=u, text=f"📢 **رسالة من الإدارة:**\n\n{update.message.text}", parse_mode="Markdown")
            except: pass
        await update.message.reply_text("✅ تم الإرسال.")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_handler))
    app.run_polling()

