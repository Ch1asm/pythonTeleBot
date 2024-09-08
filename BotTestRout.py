import os
import telebot
import logging
from pathlib import Path
from dotenv import load_dotenv
from telbot_storage_handler import StorageHandler
from gpt_handler import GptHandler
import command_parser
from allow_lists import AllowedLists
import random

# loading variables from .env file
load_dotenv("tggptbot.env")

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(os.environ.get("TG_BOT_TOKEN"))
storage = StorageHandler(Path(os.environ.get("APP_DB_PATH")))
gpt = GptHandler(os.environ.get("GPT_API_KEY"), os.environ.get("GPT_ENGINE_MODEL"))
all_list = AllowedLists(storage, float(os.environ.get("TG_BOT_ADMIN")))
boobs_words_list = ['сиськи', 'титьки', 'бюст', 'буфера', 'дойки', 'сисек', 'сиську', 'сисечку', 'сисяндры', 'титечки',
                    'грудь', 'груди']


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "It's a private bot. Contact to owner for more info.")


@bot.message_handler(content_types=['text'])
def handle_all_text(message):
    stor_answer = storage.log_message(message, None, None, None)
    if (is_boobs_included(message.text) and
            str(message.chat.id) + ".0" + str(message.message_thread_id) in all_list.allowed_chat_boobs_list):
        boobs_ans = boobs_handle(os.environ.get("APP_BOOBS_PATH"), message)
        if boobs_ans is not None:
            storage.log_message(bot.reply_to(message, boobs_ans), None, None, None)
    else:
        if str(message.chat.id) + ".0" + str(message.message_thread_id) in all_list.allowed_chat_list_text:
            if stor_answer != "":
                storage.log_message(bot.send_message(int(os.environ.get("TG_BOT_ADMIN")), stor_answer),
                                    None, None, None)
            answer = generate_bot_answer(message)
            if answer != "":
                storage.log_message(bot.reply_to(message, answer), None, None, None)


@bot.message_handler(func=lambda msg: msg.voice.mime_type == "audio/ogg", content_types=["voice"])
def handle_all_voice(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    answer = gpt.get_gpt_audio_text(downloaded_file)
    storage.log_message(message, None, file_info.file_path, answer)
    if (str(message.chat.id) + ".0" + str(message.message_thread_id)
            in all_list.allowed_chat_list_voice and answer != ""):
        storage.log_message(bot.reply_to(message, answer), None, None, None)


def generate_bot_answer(message):
    # проверка на разрешенный чат
    if str(message.chat.id) + ".0" + str(message.message_thread_id) in all_list.allowed_chat_list_text:
        if message.text.lower().startswith("$bot") and (message.from_user.id in all_list.allowed_command_user_list):
            # ветка для обработки команд
            command = command_parser.parse(message.text,
                                           message.from_user.id == float(os.environ.get("TG_BOT_ADMIN")),
                                           message.from_user.id,
                                           message.chat.id)
            if command.startswith("SELECT"):
                return storage.execute_command(command)
            elif command.startswith("UPDATE"):
                answer = storage.execute_command(command)
                all_list.update(storage)
                return answer
            else:
                return command
        if storage.checkgptstory(message, os.environ.get("APP_BOT_ID")):
            # ветка для обработки переписок с ботом
            gptdialog = storage.getmessagegptthread(message, os.environ.get("APP_BOT_ID"),
                                                    os.environ.get("GPT_SYSTEM_MESSAGE"))
            return gpt.get_gpt_text_response(gptdialog)
        return ""
    else:
        return ""


def is_boobs_included(text: str):
    for elem in boobs_words_list:
        if elem in text.lower():
            return True
    return False


def boobs_handle(boobs_pass: str, message: telebot.types.Message):
    files = os.listdir(boobs_pass)
    files = [f for f in files if os.path.isfile(os.path.join(boobs_pass, f))]
    if not files:
        return "It's a disaster! We don't have tits to show!"
    boobs_file = open(boobs_pass+random.choice(files), 'rb')
    bot.send_video(message.chat.id,
                   boobs_file,
                   reply_to_message_id=message.message_id,
                   has_spoiler=True,
                   supports_streaming=True)
    boobs_file.close()
    return None


bot.polling()
