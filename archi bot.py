import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from google import genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8830076996:AAFDcsnWVefMuOOdThnGaroRKvt4tBZXEtU"
GEMINI_API_KEY = "AQ.Ab8RN6KeKUv9dRhQs89tlncNC7OCUSgyFUhcxjtpLOIHP7SydA"

client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Salom {user.first_name}! Men Archi!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_message
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
