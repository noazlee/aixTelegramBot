# /Users/noahlee/Documents/DS Practice/AIX2/venv - conda env
import os
import logging
from questions import answer_question
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
from openai import OpenAI
import asyncio
import nest_asyncio

nest_asyncio.apply()

openai = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
tg_bot_token = os.environ['TG_BOT_TOKEN']

messages = [{
    "role":"system",
    "content":"You are a helpful assistant that answers questions about Video Games and Gamer's Hideout. Use the context given if possible and limit answers to 100 characters."
}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - $(levelname)s - %(message)s',
    level=logging.INFO
)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages.append({"role": "user", "content": update.message.text})
    completion = openai.chat.completions.create(model="gpt-4o-mini",
                                               messages=messages)
    completion_answer = completion.choices[0].message
    messages.append({"role": completion_answer.role, "content": completion_answer.content})

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                  text=completion_answer.content)
    
async def rag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recent_messages = messages[1:] if len(messages) > 1 else []
    recent_messages.append({"role": "user", "content": update.message.text})
    recent_history = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    full_question = f"System: {messages[0]['content']}\n{recent_history}"
    answer = answer_question(question=full_question, debug=True)
    
    # Append the user question and AI answer to the messages list
    messages.append({"role": "user", "content": update.message.text})
    messages.append({"role": "assistant", "content": answer})
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                  text="I am a bot, please talk to me.")
    
# Main function to run the bot
async def main() -> None:
    application = ApplicationBuilder().token(tg_bot_token).build()

    start_handler = CommandHandler('start', start)
    chat_handler = CommandHandler('chat', chat)
    mozilla_handler = CommandHandler('rag', rag)

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