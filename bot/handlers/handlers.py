# bot/handlers/handlers.py

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from ai_module.nlu import get_model_response, parse_model_response  # ✅ Теперь работает!

async def start(update, context):
    await update.message.reply_text("Бот запущен!")

async def handle_message(update, context):
    user_message = update.message.text
    text_response = get_model_response(user_message)
    result = parse_model_response(text_response)

    if result:
        await update.message.reply_text(f"Распознано: {result}")
    else:
        await update.message.reply_text("Не понял запрос.")

def start_bot():
    from bot.config import settings

    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()