import openai
import os
from dotenv import load_dotenv, find_dotenv


class OpenAIImageService:
    def __init__(self, api_key:str = None):
        _ = load_dotenv(find_dotenv())
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)

    def generate(self, prompt: str, model: str = "dall-e-3", size: str = "1024x1024", quality: str = "standard") -> str:
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        return response.data[0].url
