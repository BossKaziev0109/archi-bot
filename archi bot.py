import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# API Keys
TELEGRAM_TOKEN = "8830076996:AAGqRtRaNmsTvU-kKZQZZpPslOP6Jk153Ms"
GEMINI_API_KEY = "AQ.Ab8RN6I1EtOtm2AJZ3TxqN3d7Pb9zObMPq4HwrH5OOxlokoo4g"

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt
SYSTEM_PROMPT = """Siz Archi ismli aqlli yordamchisiz. 
Siz rus va o'zbek tillarida javob berasiz.
Foydalanuvchi qaysi tilda yozsa, shu tilda javob bering.
Siz har qanday savollarga javob bera olasiz - ta'lim, biznes, texnologiya, hayot maslahatlari va boshqa mavzularda.
Doim do'stona, mehribon va foydali bo'ling.
O'zingizni Archi deb tanishtiring."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        f"Привет! Я *Арчи* — твой умный помощник 🤖\n\n"
        f"Мен *Арчи* — сенинг ақлли ёрдамчингман 🤖\n\n"
        f"Задавай любые вопросы — отвечу на русском или узбекском!\n"
        f"Har qanday savol bering — rus yoki o'zbek tilida javob beraman!",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Арчи — твой помощник*\n\n"
        "Я могу помочь с:\n"
        "• Любыми вопросами 💬\n"
        "• Советами по бизнесу 💼\n"
        "• Обучением 📚\n"
        "• Технологиями 💻\n"
        "• И многим другим!\n\n"
        "Просто напиши свой вопрос! 😊",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.effective_user
    
    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    try:
        # Get chat history from context
        if 'history' not in context.user_data:
            context.user_data['history'] = []
        
        # Add user message to history
        context.user_data['history'].append({
            'role': 'user',
            'parts': [user_message]
        })
        
        # Keep only last 10 messages
        if len(context.user_data['history']) > 20:
            context.user_data['history'] = context.user_data['history'][-20:]
        
        # Create chat with history
        chat = model.start_chat(history=context.user_data['history'][:-1])
        
        # Send message with system prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nПользователь: {user_message}"
        response = chat.send_message(full_prompt)
        
        bot_response = response.text
        
        # Add bot response to history
        context.user_data['history'].append({
            'role': 'model',
            'parts': [bot_response]
        })
        
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "😔 Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.\n"
            "Произошла ошибка. Попробуйте снова."
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Archi bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
