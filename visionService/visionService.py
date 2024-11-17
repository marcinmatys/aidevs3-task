from abc import ABC, abstractmethod
from typing import Dict, List, Any

class VisionService(ABC):
    @abstractmethod
    def get_completion(self, prompt: str, images: List[Dict[str, Any]], model: str = "gpt-4o", temperature: float = 1, response_format: str = "text") -> str:
        pass