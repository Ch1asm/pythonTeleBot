from openai import OpenAI
import logging
import time

logger = logging.getLogger(__name__)

class GptHandler:

    client = None
    eng_model = ""
    last_text_send_time = 0
    last_voice_send_time = 0

    def __init__(self,
                 my_api_key: str,
                 engine_model: str):
        self.client = OpenAI(api_key=my_api_key)
        self.eng_model = engine_model

    def get_gpt_text_response(self, dialog: list):
        current_time = time.time()  # Текущее время в секундах
        time_since_last = current_time - self.last_text_send_time
        if time_since_last < 20:
            # Если прошло меньше 20 секунд, подождем оставшееся время
            time.sleep(20 - time_since_last)
        try:
            chat_completion = self.client.chat.completions.create(messages=dialog,
                                                                  model=self.eng_model,
                                                                  max_tokens=5000)
            self.last_text_send_time = time.time()  # запомнили время последней отправки
        except Exception as e:
            logger.exception("Нет ответа от GPT: $s", e.__repr__(), e.args)
            return "Exception from OpenAI GPT: " + str(e.__repr__()) + str(e.args)
        return chat_completion.choices[0].message.content

    def get_gpt_audio_text(self, file: bytes):
        current_time = time.time()  # Текущее время в секундах
        time_since_last = current_time - self.last_voice_send_time
        if time_since_last < 20:
            # Если прошло меньше 20 секунд, подождем оставшееся время
            time.sleep(20 - time_since_last)
        try:
            answer = self.client.audio.transcriptions.create(file=("file.ogg", file, "audio/ogg"),
                                                             model="whisper-1",
                                                             response_format="text")
            self.last_voice_send_time = time.time()
            return answer
        except Exception as e:
            logger.exception("Нет ответа от whisper: %s", e.__repr__(), e.args)
            return "Exception from OpenAI Whisper: " + str(e.__repr__()) + str(e.args)
