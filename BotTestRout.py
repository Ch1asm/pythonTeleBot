import os
import telebot
import logging
from pathlib import Path
from dotenv import load_dotenv
from telbot_storage_handler import StorageHandler
from gpt_handler import GptHandler

# loading variables from .env file
load_dotenv("tggptbot.env")

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(os.environ.get("TG_BOT_TOKEN"))
storage = StorageHandler(Path(os.environ.get("APP_DB_PATH")))
gpt = GptHandler(os.environ.get("GPT_API_KEY"), os.environ.get("GPT_ENGINE_MODEL"))

allowed_chat_list_text = [int(os.environ.get("TG_BOT_ADMIN")),]
allowed_chat_list_voice = [int(os.environ.get("APP_MASTER_CHAT")), int(os.environ.get("TG_BOT_ADMIN"))]
allowed_comand_userst_list = [int(os.environ.get("TG_BOT_ADMIN")),]


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Пока я общаюсь только с Создателем")


@bot.message_handler(content_types=['text'])
def handle_all_text(message):
    stor_answer = storage.logtextmessage(message)
    if message.chat.id in allowed_chat_list_text:
        if stor_answer != "":
            storage.logtextmessage(bot.send_message(int(os.environ.get("TG_BOT_ADMIN")), stor_answer))
        answer = generate_bot_answer(message)
        if answer != "":
            storage.logtextmessage(bot.reply_to(message, answer))


@bot.message_handler(func=lambda msg: msg.voice.mime_type == "audio/ogg", content_types=["voice"])
def handle_all_voice(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    if message.chat.id in allowed_chat_list_voice:
        answer = gpt.get_gpt_audio_text(downloaded_file)
        if answer != "":
            storage.logtextmessage(bot.reply_to(message, answer))


def generate_bot_answer(message):
    # проверка на разрешенный чат
    if message.chat.id in allowed_chat_list_text:
        if message.text.lower().startswith("/com") and message.from_user.id in allowed_comand_userst_list:
            # ветка для обработки команд
            if message.text.lower().startswith("/com sys_mes"):
                return storage.command_set_chat_system_message(message)
            return "bad command"
        if storage.checkgptstory(message, os.environ.get("APP_BOT_ID")):
            # ветка для обработки переписок с ботом
            gptdialog = storage.getmessagegptthread(message, os.environ.get("APP_BOT_ID"),
                                                    os.environ.get("GPT_SYSTEM_MESSAGE"))
            return gpt.get_gpt_text_response(gptdialog)
        return ""
    else:
        return ""


bot.polling()
