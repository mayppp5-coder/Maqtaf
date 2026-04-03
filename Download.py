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

# --- وظائف جلب البيانات وتصحيح الأسماء ---
def get_stories_data():
    library = {}
    for file in os.listdir():
        if file.endswith(".txt") and "_" in file and file != USERS_FILE:
            try:
                parts_name = file.replace(".txt", "").split("_", 1)
                raw_category = parts_name[0].strip()
                # تنظيف القسم من أي رموز غير مرئية أو نقاط في البداية
                category = "".join(char for char in raw_category if char.isalnum() or char in [" "])
                title = parts_name[1].strip()
                
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
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- معالجة الأزرار ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()
    all_data = get_stories_data()

    if data == "admin_panel" and user_id == ADMIN_ID:
        count = len(get_users_list())
        keyboard = [[InlineKeyboardButton("📢 إرسال إشعار", callback_data="admin_broadcast")], [InlineKeyboardButton("🔙 عودة", callback_data="back_home")]]
        await query.edit_message_text(f"📊 **لوحة التحكم**\n👤 المشتركين: {count}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data.startswith("maincat_"):
        parts = data.split("_")
        cat = parts[1]
        page_num = int(parts[2]) if len(parts) > 2 else 0
        
        if cat in all_data:
            titles = list(all_data[cat].keys())
            per_page = 5
            start_idx = page_num * per_page
            end_idx = start_idx + per_page
            current_titles = titles[start_idx:end_idx]
            
            # عرض القصص بشكل عريض (زر واحد لكل سطر)
            keyboard = [[InlineKeyboardButton(f"📖 {t}", callback_data=f"listparts_{cat}_{t}")] for t in current_titles]
            
            # أزرار التنقل (التالي والسابق)
            nav_buttons = []
            if page_num > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"maincat_{cat}_{page_num-1}"))
            if end_idx < len(titles):
                nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"maincat_{cat}_{page_num+1}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
                
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_home")])
            await query.edit_message_text(f"📍 قسم: **{cat}**\nصفحة: {page_num + 1}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.answer("هذا القسم فارغ حالياً.. ⏳", show_alert=True)

    elif data.startswith("listparts_"):
        _, cat, title = data.split("_", 2)
        parts = all_data[cat][title]
        
        if len(parts) == 1:
            keyboard = [[InlineKeyboardButton("🔙 عودة للقسم", callback_data=f"maincat_{cat}_0")]]
            if len(parts[0]) > 1:
                keyboard.insert(0, [InlineKeyboardButton("تكملة البارت ⬇️", callback_data=f"read_{cat}_{title}_0_1")])
            await query.edit_message_text(f"📖 **{title}**\n\n{parts[0][0]}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            keyboard = [[InlineKeyboardButton(f"📖 البارت {i+1}", callback_data=f"read_{cat}_{title}_{i}_0")] for i in range(len(parts))]
            keyboard.append([InlineKeyboardButton("🔙 عودة للقسم", callback_data=f"maincat_{cat}_0")])
            await query.edit_message_text(f"📚 رواية: **{title}**\nاختر الجزء:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg_text = " ".join(context.args)
    if not msg_text:
        await update.message.reply_text("❌ استخدم: `/send نص الرسالة`")
        return
    users = get_users_list()
    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg_text)
            count += 1
        except: pass
    await update.message.reply_text(f"✅ تم الإرسال إلى {count} مستخدم.")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_broadcast))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
