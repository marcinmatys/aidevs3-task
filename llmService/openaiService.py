import openai
import os
from dotenv import load_dotenv, find_dotenv
from .completionService import CompletionService


class OpenAIService(CompletionService):
    def __init__(self, api_key:str = None):
        _ = load_dotenv(find_dotenv())
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)

    def get_completion(self, prompt: str, model: str = "gpt-4o", temperature: int = 1, response_format: str = "text") -> str:
        messages = [{"role": "system", "content": prompt}]
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": response_format}
        )
        return response.choices[0].message.content
