from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
import threading
import time
import openai
import csv
import os
import io

load_dotenv()

telegram_token = os.getenv('TELEGRAM_TOKEN')
openai.api_key = os.getenv('OPENAI_API_KEY')


updater = Updater(
    token=telegram_token, use_context=True)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет! Я умею делать рекламу. Пришли мне ключевую фразу, а я придумаю 20 рекламных объявлений.")


def process_message(update: Update, context: CallbackContext):
    # Retrieve message
    message = update.message.text
    chat_id = update.effective_chat.id

    # Start a new thread to handle the OpenAI API call and CSV generation
    thread = threading.Thread(
        target=generate_csv, args=(message, chat_id, context))
    thread.start()

    # Send progress messages
    context.bot.send_message(
        chat_id=chat_id, text=f"Составляю объявления для ключевой фразы {message}")
    time.sleep(3)
    context.bot.send_message(chat_id=chat_id, text="Придумываю заголовки...")
    time.sleep(3)
    context.bot.send_message(chat_id=chat_id, text="Добавляю мемы...")
    time.sleep(3)
    context.bot.send_message(chat_id=chat_id, text="Испарвляю опечатки...")
    while thread.is_alive():
        time.sleep(7)
        context.bot.send_message(chat_id=chat_id, text="Почти готово...")
    context.bot.send_message(chat_id=chat_id, text="Готово!")


def generate_csv(message, chat_id, context):
    # Your existing code to call the OpenAI API and generate the CSV
    prompt = """Act as a copywriter and Search Engine Marketing expert. 
    Please compose 20 creatives for the following key phrase: {}.
    Each creative should consist of a header(up to 56 symbols) and a body (up to 75 symbols).
    Headers is the main catch phrase - it should attract attention.
    Body expands on the catch phrase and provides the details.
    Creatives should be in the same language as the key phrase.
    Please format them as a CSV file with 2 columns: header and body.

    Example:
    header,body
    "Great Product","The most inovative product online. Buy now!"
    """.format(message)

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
    )

    answer = res['choices'][0]['message']['content']
    lines = answer.split('\n')
    creatives = [next(csv.reader([line])) for line in lines]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(creatives)
    csv_content = output.getvalue()
    output.close()

    # Create a file and send it back
    context.bot.send_document(chat_id=chat_id, document=io.BytesIO(
        csv_content.encode()), filename='creatives.csv')


start_handler = CommandHandler('start', start)
message_handler = MessageHandler(
    Filters.text & (~Filters.command), process_message)

# Add handlers
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(message_handler)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
