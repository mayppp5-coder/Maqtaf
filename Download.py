import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8669525251:AAGQSRVc_0_jEiZJnX7p_KoVAoULuukXS0s"
KEY = "AIzaSyAWys1l4PQ4AIhxdjl8WC2txctV3UQ15Uw"

genai.configure(api_key=KEY)

async def check_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # هذه الدالة ستجلب كل الموديلات المتاحة لمفتاحك الخاص
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        response = "✅ الموديلات المتاحة لحسابك هي:\n\n" + "\n".join(available_models)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"❌ فشل جلب الموديلات. السبب:\n{str(e)}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("test", check_models))
    app.run_polling()
