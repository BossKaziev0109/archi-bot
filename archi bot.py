import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8830076996:AAGqRtRaNmsTvU-kKZQZZpPslOP6Jk153Ms"
GEMINI_API_KEY = "AIzaSyAb8RN6I1EtOtm2AJZ3TxqN3d7Pb9zObMPq4HwrH5OOxlokoo4g"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Salom {user.first_name}! Men Archi!\n\nПривет {user.first_name}! Я Арчи!\n\nЗадавай любые вопросы!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    try:
        prompt = f"Ты помощник Арчи. Отвечай на языке вопроса (русский/узбекский). Вопрос: {user_message}"
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Ошибка. Попробуйте снова.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
