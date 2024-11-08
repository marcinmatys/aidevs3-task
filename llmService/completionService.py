from abc import ABC, abstractmethod

class CompletionService(ABC):
    @abstractmethod
    def get_completion(self, prompt: str, model: str = "gpt-4o", temperature: float = 1, response_format: str = "text") -> str:
        pass