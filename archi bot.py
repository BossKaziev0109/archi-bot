import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from tavily import TavilyClient
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = "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"
TAVILY_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_histories = {}

SYSTEM_PROMPT = """Ты Арчи — личный ассистент Азизбека Казиева.
Ты знаешь всё — как энциклопедия, врач, юрист, финансист, техник и друг в одном.

ГЛАВНЫЕ ПРАВИЛА:
— Отвечай коротко и точно. Без лишних слов.
— Если есть данные из поиска — используй ТОЛЬКО их.
— Никогда не говори "не знаю" — дай лучший ответ.
— Отвечай на языке пользователя (русский, узбекский, английский).
— Обращайся: Азизбек.
— Эмодзи используй умеренно.

НА ЛЮБОЙ ВОПРОС — ДАВАЙ КОНКРЕТНЫЙ ОТВЕТ:
— Медицина: симптомы, причины, что делать
— Юридические: объясни закон простыми словами
— Финансы: конкретные цифры и советы
— Техника: характеристики, цены, сравнение
— Кулинария: рецепт по шагам
— Психология: поддержка и советы
— Наука: объяснение простым языком
— История: факты и даты
— Курсы валют: конкретная цифра из поиска
— Погода: температура и осадки коротко
— Новости: главное в 1-2 предложениях"""

MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🌤 Погода"), KeyboardButton("💵 Курс валют")],
        [KeyboardButton("🚗 Пробки"), KeyboardButton("🍽 Рестораны")],
        [KeyboardButton("📰 Новости"), KeyboardButton("📱 Техника")],
        [KeyboardButton("⚽ Спорт"), KeyboardButton("🎬 Кино")],
    ],
    resize_keyboard=True
)

SEARCH_KEYWORDS = [
    "курс", "доллар", "евро", "рубль", "сум", "биткоин", "крипто", "акции",
    "цена", "стоимость", "инфляция", "банк", "кредит",
    "погода", "температура", "дождь", "снег", "ветер", "прогноз",
    "новости", "сегодня", "сейчас", "произошло", "случилось",
    "война", "политика", "выборы", "президент", "правительство",
    "ресторан", "кафе", "отель", "магазин", "аптека",
    "пробки", "дорога", "маршрут", "транспорт",
    "телефон", "iphone", "samsung", "xiaomi", "ноутбук", "компьютер",
    "машина", "авто", "автомобиль", "toyota", "bmw", "mercedes",
    "футбол", "баскетбол", "теннис", "хоккей", "бокс", "матч", "счёт",
    "фильм", "кино", "сериал", "музыка", "песня", "артист", "концерт",
    "здоровье", "болезнь", "симптом", "лечение", "лекарство",
    "путешествие", "виза", "билет", "самолёт", "туризм",
    "ob-havo", "yangiliklar", "narx", "bugun", "hozir", "dollar", "kurs",
    "weather", "news", "price", "today", "current", "latest", "bitcoin"
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
        f"Salom {user.first_name}! 👋\n"
        f"Привет {user.first_name}! Я Арчи 🤖\n\n"
        f"Знаю всё — отвечаю быстро и точно!\n\n"
        f"🌤 Погода  💵 Курсы валют\n"
        f"🚗 Пробки  🍽 Рестораны\n"
        f"📰 Новости  📱 Техника\n"
        f"⚽ Спорт  🎬 Кино\n"
        f"🏥 Медицина  ⚖️ Юридические\n"
        f"🍳 Рецепты  ✈ Путешествия\n\n"
        f"Спрашивай что угодно!",
        reply_markup=MENU
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text

    if user.id not in user_histories:
        user_histories[user.id] = []

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    search_context = ""
    if needs_search(user_message):
        try:
            results = tavily_client.search(
                query=user_message,
                max_results=5,
                search_depth="advanced"
            )
            if results and results.get("results"):
                search_context = "\n\n[Актуальные данные из интернета]:\n"
                for r in results["results"]:
                    search_context += f"• {r['title']}: {r['content'][:300]}\n"
        except Exception as e:
            logger.error(f"Search error: {e}")

    full_message = user_message
    if search_context:
        full_message += search_context

    user_histories[user.id].append({"role": "user", "content": full_message})

    if len(user_histories[user.id]) > 10:
        user_histories[user.id] = user_histories[user.id][-10:]

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user.id]
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=600,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        user_histories[user.id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply, reply_markup=MENU)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй ещё раз 🔄", reply_markup=MENU)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
