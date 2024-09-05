from openai import OpenAI
import logging


class GptHandler:

    client = None
    eng_model = ""

    def __init__(self,
                 my_api_key: str,
                 engine_model: str):
        self.client = OpenAI(api_key=my_api_key)
        self.eng_model = engine_model

    def get_gpt_text_response(self, dialog: list):
        try:
            chat_completion = self.client.chat.completions.create(messages=dialog,
                                                                  model=self.eng_model,
                                                                  max_tokens=5000)
        except Exception as e:
            logging.debug("Нет ответа от GPT: ", e.__repr__(), e.args)
            return "Exception from OpenAI GPT: " + str(e.__repr__()) + str(e.args)
        return chat_completion.choices[0].message.content

    def get_gpt_audio_text(self, file: bytes):
        try:
            return self.client.audio.transcriptions.create(file=("file.ogg", file, "audio/ogg"),
                                                           model="whisper-1",
                                                           response_format="text")
        except Exception as e:
            logging.debug("Нет ответа от whisper: ", e.__repr__(), e.args)
            return "Exception from OpenAI Whisper: " + str(e.__repr__()) + str(e.args)
