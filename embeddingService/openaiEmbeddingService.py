import openai
import os
from dotenv import load_dotenv, find_dotenv
from .embeddingService import EmbeddingService
from typing import Dict, List, Any


class OpenAIEmbeddingService(EmbeddingService):

    def __init__(self, api_key:str = None):
        _ = load_dotenv(find_dotenv())
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)

    def get_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        response = self.client.embeddings.create(
            model=model,
            input=texts
            #dimensions=3072
        )

        return [data.embedding for data in response.data]



