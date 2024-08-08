import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
import nest_asyncio
from dotenv import load_dotenv
import groq

# Load environment variables
load_dotenv()

nest_asyncio.apply()
tg_bot_token = os.getenv('TG_BOT_TOKEN')
groq_api_key = os.getenv('GROQ_API_KEY')

# Initialize Groq client
client = groq.Groq(api_key=groq_api_key)

messages = [{
    "role": "system",
    "content": "You are a helpful assistant that answers questions about Video Games and Gamer's Hideout. Use the context given if possible and limit answers to 100 characters."
}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    messages.append({"role": "user", "content": user_message})
    
    # Generate response using Groq
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant", 
        max_tokens=100,
        temperature=0.7,
    )
    
    assistant_response = chat_completion.choices[0].message.content
    
    messages.append({"role": "assistant", "content": assistant_response})
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=assistant_response)

async def main() -> None:
    application = ApplicationBuilder().token(tg_bot_token).build()
    chat_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat)
    application.add_handler(chat_handler)
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "asyncio.run() cannot be called from a running event loop":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise