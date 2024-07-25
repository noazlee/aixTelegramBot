# /Users/noahlee/Documents/DS Practice/AIX2/venv - conda env
import os
import logging
import pandas as pd
import numpy as np
from questions import answer_question
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
from openai import OpenAI
import asyncio
import nest_asyncio
import pickle
import faiss

nest_asyncio.apply()

openai = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
tg_bot_token = os.environ['TG_BOT_TOKEN']

messages = [{
    "role":"system",
    "content":"You are a helpful assistant that answers questions."
}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - $(levelname)s - %(message)s',
    level=logging.INFO
)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages.append({"role":"user","content":update.message.text})
    completion = openai.chat.completions.create(model="gpt-4.0-mini",
                                               messages=messages)
    completion_answer=completion.choices[0].message
    messages.append(completion_answer)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                  text=completion_answer.content)
    
async def rag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = answer_question(df, question=update.message.text, debug=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                  text="I am a bot, please talk to me.")
    
# Main function to run the bot
async def main() -> None:
    application = ApplicationBuilder().token(tg_bot_token).build()

    start_handler = CommandHandler('start', start)
    chat_handler = CommandHandler('chat', chat)
    mozilla_handler = CommandHandler('mozilla', mozilla)

    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    application.add_handler(mozilla_handler)

    await application.run_polling()

# Check if the script is run directly (not imported)
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "asyncio.run() cannot be called from a running event loop":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise