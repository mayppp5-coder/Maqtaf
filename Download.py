import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
TELEGRAM_TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
ADMIN_ID = 1077989275 
USERS_FILE = "users.txt"

logging.basicConfig(level=logging.INFO)

# --- وظائف إدارة المستخدمين ---
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

# --- وظائف جلب البيانات ---
def get_stories_data():
    library = {}
    for file in os.listdir():
        if file.endswith(".txt") and "_" in file and file != USERS_FILE:
            try:
                parts_name = file.replace(".txt", "").split("_", 1)
                category, title = parts_name[0].strip(), parts_name[1].strip()
                if category not in library: library[category] = {}
                with open(file, 'r', encoding='utf-8') as f:
                    main_parts = f.read().split("NEXT_PART")
                    parsed_parts = [[page.strip() for page in p.split("===") if page.strip()] for p in main_parts if p.strip()]
                    library[category][title.replace("_", " ")] = parsed_parts
            except: pass
    return library

# --- الأوامر الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📚 قصص خيالية", callback_data="maincat_خيالية")],
        [InlineKeyboardButton("📚 قصص رعب", callback_data="maincat_رعب")],
        [InlineKeyboardButton("📚 قصص دينية", callback_data="maincat_دينية")],
        [InlineKeyboardButton("✅ قصص حقيقية", callback_data="maincat_حقيقية")],
        [InlineKeyboardButton("📚 قصص تاريخية", callback_data="maincat_تاريخية")],
        [InlineKeyboardButton("📚 روايات", callback_data="maincat_روايات")],
        [InlineKeyboardButton("💡", callback_data="maincat_نصيحة")]
    ]
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 إحصائيات الأدمن", callback_data="admin_panel")])
        
    msg = "🌟 **مرحباً بك في مكتبة القصص**\n\nاختر القسم الذي ترغب في تصفحه:"
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- ميزة الإذاعة (Broadcast) ---
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    msg_text = " ".join(context.args)
    if not msg_text:
        await update.message.reply_text("❌ يرجى كتابة الرسالة بعد الأمر.\nمثال: `/send مرحباً أيها القراء`", parse_mode="Markdown")
        return

    users = get_users_list()
    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg_text)
            count += 1
        except: pass
    
    await update.message.reply_text(f"✅ تم إرسال الإشعار إلى {count} مستخدم.")

# --- معالجة الأزرار ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()
    all_data = get_stories_data()

    if data == "admin_panel" and user_id == ADMIN_ID:
        count = len(get_users_list())
        keyboard = [
            [InlineKeyboardButton("📢 إرسال إشعار للجميع", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 عودة للقائمة", callback_data="back_home")]
        ]
        await query.edit_message_text(f"📊 **لوحة التحكم**\n\n👤 المشتركين: {count}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data == "admin_broadcast" and user_id == ADMIN_ID:
        await query.edit_message_text("📢 **طريقة الإرسال:**\n\nاكتب في الشات الأمر التالي:\n`/send` وبعده رسالتك.\n\n*مثال:*\n`/send تم إضافة قصة جديدة في قسم الرعب!`", parse_mode="Markdown")

    elif data.startswith("maincat_"):
        cat = data.replace("maincat_", "")
        if cat in all_data:
            keyboard = [[InlineKeyboardButton(f"🔖 {t}", callback_data=f"listparts_{cat}_{t}")] for t in all_data[cat].keys()]
            keyboard.append([InlineKeyboardButton("🔙 الرئيسية", callback_data="back_home")])
            await query.edit_message_text(f"📍 قسم: {cat}", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer("قريباً.. ⏳", show_alert=True)

    elif data.startswith("listparts_"):
        _, cat, title = data.split("_", 2)
        parts = all_data[cat][title]
        keyboard = [[InlineKeyboardButton(f"📖 البارت {i+1}", callback_data=f"read_{cat}_{title}_{i}_0")] for i in range(len(parts))]
        keyboard.append([InlineKeyboardButton("🔙 عودة للقسم", callback_data=f"maincat_{cat}")])
        await query.edit_message_text(f"📚 رواية: **{title}**\nاختر البارت:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
        await query.edit_message_text(f"📖 **{title} - البارت {p_idx+1}**\n\n{pages[s_idx]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "back_home":
        await start(update, context)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_broadcast)) # أمر الإرسال
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
