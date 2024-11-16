import openai
from dotenv import load_dotenv, find_dotenv
import os
from .asrService import ASRService

_ = load_dotenv(find_dotenv())

class OpenaiASRService(ASRService):

    def __init__(self):
        _ = load_dotenv(find_dotenv())
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)

    def get_transcription(self, audio):

        result = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio
        )

        return result.text