from abc import ABC, abstractmethod

class ASRService(ABC):
    @abstractmethod
    def get_transcription(self, audio) -> str:
        pass