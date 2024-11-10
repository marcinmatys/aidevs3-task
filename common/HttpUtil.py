import requests
import logging
from urllib.parse import urljoin
from typing import Dict, Any

from common.logger_config import setup_logger


class HttpUtil:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = setup_logger('HttpUtil')

    def getData(self, endpoint=None) -> Any:

        full_url = self.base_url if endpoint is None else urljoin(self.base_url, endpoint)

        try:
            self.logger.info(f"Pobieranie danych z {full_url}")
            response = requests.get(full_url)
            response.raise_for_status()
            #self.logger.info(f"Pobrano dane: {response.text.strip()}")
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Błąd podczas pobierania danych: {str(e)}")
            raise

    def sendForm(self, data, endpoint=None) -> str:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"
        }

        full_url = self.base_url if endpoint is None else urljoin(self.base_url, endpoint)

        try:
            response = requests.post(full_url, data=data, headers=headers)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            error_msg = f"Błąd podczas wysyłania żądania: {str(e)}"
            self.logger.error(error_msg)

    def sendData(self, data, endpoint=None) -> Dict[str, Any]:


        full_url = self.base_url if endpoint is None else urljoin(self.base_url, endpoint)

        try:
            self.logger.info(f"Wysyłanie żądania do {full_url}")
            self.logger.info(f"Payload: {data}")
            response = requests.post(full_url, json=data)
            response.raise_for_status()
            response_data = response.json()
            return response_data

        except requests.exceptions.RequestException as e:
            error_msg = f"Błąd podczas wysyłania danych: {str(e)}"
            self.logger.error(error_msg)
            return response.content
