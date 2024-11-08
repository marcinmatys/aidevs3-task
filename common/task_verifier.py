import requests
import os
from dotenv import load_dotenv
from typing import Union, Dict, Any
from common.logger_config import setup_logger


class TaskVerifier:
    def __init__(self, base_url:str):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        self.verify_url = f"{base_url}/verify"
        self.logger = setup_logger('TaskVerifier')

    def verify(self, task_name: str, answer: Union[str, list, dict]) -> Dict[str, Any]:
        """
        Weryfikuje odpowiedź poprzez API.

        Args:
            task_name (str): Nazwa zadania
            answer: Odpowiedź do zweryfikowania (może być string, lista lub słownik)

        Returns:
            Dict[str, Any]: Odpowiedź z API zawierająca kod i wiadomość
        """
        payload = {
            "task": task_name,
            "apikey": self.api_key,
            "answer": answer
        }

        # Logowanie payloadu (ukrywamy apikey)
        safe_payload = payload.copy()
        safe_payload["apikey"] = "***"
        self.logger.info(f"Wysyłanie żądania do {self.verify_url}")
        self.logger.info(f"Payload: {safe_payload}")

        try:
            response = requests.post(self.verify_url, json=payload)
            response.raise_for_status()
            response_data = response.json()

            # Logowanie odpowiedzi
            self.logger.info(f"Odpowiedź: {response_data}")

            return response_data

        except requests.exceptions.RequestException as e:
            error_msg = f"Błąd podczas wysyłania żądania: {str(e)}"
            self.logger.error(error_msg)
            return {"code": -1, "message": error_msg}
        except ValueError as e:
            error_msg = f"Błąd podczas parsowania odpowiedzi: {str(e)}"
            self.logger.error(error_msg)
            return {"code": -1, "message": error_msg}