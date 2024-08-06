# /Users/noahlee/Documents/DS Practice/AIX2/venv - conda env
import os
import logging
from questions import answer_question
from telegram import Update
from telegram.ext import (
 ApplicationBuilder,
 CommandHandler,
 ContextTypes,
 MessageHandler,
 filters,
)
from openai import OpenAI
import asyncio
import nest_asyncio
import requests
from functions import functions, run_function
import json
from deepgram import Deepgram

nest_asyncio.apply()

openai = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
tg_bot_token = os.environ['TG_BOT_TOKEN']
deepgram_api_key = os.environ['DEEPGRAM_API_KEY']


CODE_PROMPT = """
Here are some input:output examples for sentiment analysis. Please use these and follow the styling for
future requests that you think are pertinent to the request.
// SAMPLE 1 
Input: What is the sentiment for The Legend of Zelda: Breath of the Wild?
Output: The Legend of Zelda: Breath of the Wild has an overall very positive sentiment with a metacritic score of 97.

// SAMPLE 2
Input: How is Pokemon Shining Pearl?
Output: Pokemon Shining Pearl has an overall mediocre sentiment with a metacritic score of 73.
"""

examples = [
    {"role": "user", "content": "What is Gamers' Hideout?"},
    {"role": "assistant", "content": "Gamers' Hideout is the most popular video game seller in Malaysia with various locations and services tailored for gamers. It operates both as a retail store and a gaming lounge, catering to different aspects of gaming culture and community."},
]

messages = [{
    "role":"system",
    "content":"You are a helpful assistant that answers questions about Video Games and Gamer's Hideout. Use the context given if possible and limit answers to 100 characters."
},
{
    "role": "system",
    "content": CODE_PROMPT
}]
messages.extend(examples)

logging.basicConfig(
    format='%(asctime)s - %(name)s - $(levelname)s - %(message)s',
    level=logging.INFO
)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages.append({"role": "user", "content": update.message.text})
    initial_response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=functions
    )
    initial_response_message = initial_response.choices[0].message
    messages.append(initial_response_message)

    final_response = None
    tool_calls = initial_response_message.tool_calls

    if tool_calls:
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            response = run_function(name, args)
            print(tool_calls)
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": name,
                "content": str(response),
            })

        # Generate the final response
        final_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        final_answer = final_response.choices[0].message

        # Send the final response if it exists
        if final_answer:
            messages.append(final_answer)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=final_answer.content)
        else:
            # Send an error message if something went wrong
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Something went wrong, please try again'
            )
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=initial_response_message.content)

async def transcribe_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice_id = update.message.voice.file_id
    file_path = f"voice_note_{voice_id}.ogg"
    tts_file_path = f"response_{voice_id}.mp3"

    if voice_id:
        try:
            file = await context.bot.get_file(voice_id)
            await file.download_to_drive(file_path)
            await update.message.reply_text("Voice note downloaded, transcribing now")
            
            with open(file_path, 'rb') as audio:
                source = {"buffer": audio, "mimetype": 'audio/ogg'}
                options = {'punctuate': True, 'language': 'en-US'}
                
                # Initialize Deepgram client within the function
                deepgram = Deepgram(deepgram_api_key)
                response = await deepgram.transcription.prerecorded(source, options)
                
            transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
            
            messages.append({"role": "user", "content": transcript})
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            response_message = response.choices[0].message
            messages.append(response_message)
            
            await update.message.reply_text(f"Transcript finished:\n{transcript}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response_message.content)
            
            # Text-to-Speech (TTS) Conversion
            tts_response = requests.post(
                'https://api.deepgram.com/v1/speak',
                headers={
                    'Authorization': f'Token {deepgram_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'text': response_message.content
                }
            )

            if tts_response.status_code != 200:
                raise Exception(f"TTS request failed: {tts_response.status_code} {tts_response.text}")

            with open(tts_file_path, 'wb') as tts_file:
                tts_file.write(tts_response.content)

            # Send TTS audio response
            with open(tts_file_path, 'rb') as tts_audio:
                await context.bot.send_voice(chat_id=update.effective_chat.id, voice=tts_audio)
            
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)

        finally:
            # Clean up temporary files
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(tts_file_path):
                os.remove(tts_file_path)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please send a voice message to transcribe.")
      

async def rag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recent_messages = messages[1:] if len(messages) > 1 else []
    recent_messages.append({"role": "user", "content": update.message.text})
    recent_history = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    full_question = f"System: {messages[0]['content']} in Gamer's hideout. Previous messages: \n{recent_history}"
    answer = answer_question(question=full_question, debug=True)
    
    # Append the user question and AI answer to the messages list
    messages.append({"role": "user", "content": update.message.text})
    messages.append({"role": "assistant", "content": answer})
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = openai.images.generate(prompt=update.message.text,
                                    model="dall-e-3",
                                    n=1,
                                    size="1024x1024")
    image_url = response.data[0].url
    image_response = requests.get(image_url)
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=image_response.content)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                  text="I am a bot, please talk to me.")
    
# Main function to run the bot
async def main() -> None:
    application = ApplicationBuilder().token(tg_bot_token).build()

    start_handler = CommandHandler('start', start)
    image_handler = CommandHandler('image', image)
    chat_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat)
    voice_handler = MessageHandler(filters.VOICE, transcribe_message)
    rag_handler = CommandHandler('rag', rag)


    application.add_handler(start_handler)
    application.add_handler(image_handler)
    application.add_handler(chat_handler)
    application.add_handler(voice_handler)
    application.add_handler(rag_handler)

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