from abc import ABC, abstractmethod
from typing import Dict, List, Any


class EmbeddingService(ABC):
    @abstractmethod
    def get_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        pass