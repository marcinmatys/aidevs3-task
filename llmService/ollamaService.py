import ollama
from .completionService import CompletionService


class OllamaService(CompletionService):

    def get_completion(self, prompt: str, model: str = "gpt-4o", temperature: float = 1, response_format: str = "text") -> str:
        response = ollama.chat(model='gemma2:2b', messages=[
            {
                'role': 'system',
                'content': prompt,
            },
        ])
        return response['message']['content']


