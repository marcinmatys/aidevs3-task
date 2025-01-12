import requests
import os
from dotenv import load_dotenv
from typing import Union, Dict, Any
from common.logger_config import setup_logger
import json


class TaskVerifier:
    def __init__(self, base_url:str, task_name:str):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        self.base_url = base_url
        self.task_name = task_name
        self.logger = setup_logger('TaskVerifier')


    def verify(self, answer: Union[str, list, dict], endpoint:str, log_payload:bool = True) -> Dict[str, Any]:
        """
        Weryfikuje odpowiedź poprzez API.

        Args:
            task_name (str): Nazwa zadania
            answer: Odpowiedź do zweryfikowania (może być string, lista lub słownik)

        Returns:
            Dict[str, Any]: Odpowiedź z API zawierająca kod i wiadomość
        """
        payload = {
            "task": self.task_name,
            "apikey": self.api_key,
            "answer": answer
        }

        verify_url = self.base_url + ("/verify" if endpoint is None else endpoint)

        # Logowanie payloadu (ukrywamy apikey)
        safe_payload = payload.copy()
        safe_payload["apikey"] = "***"
        self.logger.info(f"Wysyłanie żądania do {verify_url}")
        if log_payload :
            self.logger.info(f"Payload: {safe_payload}")

        try:
            response = requests.post(verify_url, json=payload)
            response.raise_for_status()
            response_data = response.json()

            # Logowanie odpowiedzi
            self.logger.info(f"Odpowiedź: {response_data}")

            return response_data

        except requests.exceptions.RequestException as e:
            error_msg = f"Błąd podczas wysyłania żądania: {str(e)}"
            self.logger.error(error_msg)
            decoded_content = response.content.decode('utf-8')
            self.logger.error(f"error content: {decoded_content}")
            return json.loads(decoded_content)
            #raise
        except ValueError as e:
            error_msg = f"Błąd podczas parsowania odpowiedzi: {str(e)}"
            self.logger.error(error_msg)
            raise