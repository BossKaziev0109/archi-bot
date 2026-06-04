import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from tavily import TavilyClient
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = "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"
TAVILY_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_histories = {}

SYSTEM_PROMPT = """Сен Арчи — Азизбек Казиевнинг шахсий ассистентисан.
Ты Арчи — личный ассистент Азизбека Казиева.
Ты умный, дружелюбный, всегда готов помочь.
Отвечай на том языке на котором пишет пользователь — русский, узбекский или английский.
Если тебе дают результаты поиска из интернета — используй их для точного ответа.
Обращайся к пользователю по имени Азизбек."""

SEARCH_KEYWORDS = [
    "погода", "курс", "доллар", "цена", "новости", "сегодня", "сейчас",
    "пробки", "ресторан", "кафе", "политика", "авто", "машина", "техника",
    "телефон", "iphone", "samsung", "футбол", "спорт", "фильм", "кино",
    "ob-havo", "yangiliklar", "narx", "bugun", "hozir"
]

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

def needs_search(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SEARCH_KEYWORDS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = []
    await update.message.reply_text(
        f"Salom {user.first_name}! Men Archi — sening shaxsiy yordamchingman! 🤖\n\n"
        f"Привет {user.first_name}! Я Арчи — твой личный ассистент! 🤖\n\n"
        f"Я могу:\n"
        f"🌤 Погода в реальном времени\n"
        f"💵 Курсы валют\n"
        f"🚗 Пробки на дорогах\n"
        f"🍽 Рестораны и кафе\n"
        f"📰 Новости и политика\n"
        f"📱 Техника и авто\n"
        f"💬 И всё что угодно!\n\n"
        f"Спрашивай!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text

    if user.id not in user_histories:
        user_histories[user.id] = []

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    search_results = ""
    if needs_search(user_message):
        try:
            results = tavily_client.search(query=user_message, max_results=3)
            if results and results.get("results"):
                search_results = "\n\nДанные из интернета:\n"
                for r in results["results"]:
                    search_results += f"- {r['title']}: {r['content'][:200]}\n"
        except Exception as e:
            logger.error(f"Search error: {e}")

    full_message = user_message + search_results
    user_histories[user.id].append({"role": "user", "content": full_message})

    if len(user_histories[user.id]) > 20:
        user_histories[user.id] = user_histories[user.id][-20:]

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user.id]
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        reply = response.choices[0].message.content
        user_histories[user.id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
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
