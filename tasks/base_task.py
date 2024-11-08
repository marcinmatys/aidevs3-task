from abc import ABC, abstractmethod
from typing import Dict, Any
from common.task_verifier import TaskVerifier
import requests
from common.logger_config import setup_logger

class BaseTask(ABC):
    def __init__(self, base_url: str = None, task_name = None):
        self.verifier = TaskVerifier(base_url)
        self.logger = setup_logger(self.__class__.__name__)
        self.task_name = task_name
        self.base_url = base_url

    def verify(self, data: Any) -> Dict[str, Any]:
        """
        Verify the task using the verifier.
        """
        return self.verifier.verify(self.task_name, data)

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Implementuje rozwiązanie konkretnego zadania

        Returns:
            Dict[str, Any]: Wynik weryfikacji zadania
        """
        pass
