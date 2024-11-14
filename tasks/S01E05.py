from common.HttpUtil import HttpUtil
from common.logger_config import setup_logger
from llmService.ollamaService import OllamaService
from .base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S01E05(BaseTask):
    def __init__(self):
        super().__init__(base_url,"CENZURA")

    def run(self) -> Dict[str, Any]:

        http_util = HttpUtil(base_url)

        data = http_util.getData(f"/data/{api_key}/cenzura.txt")
        self.logger.info(f"data \n {data}")

        prompt = f"""
        In below context, Replace firstname and lastname, age, street name and number, city to word CENZURA.
        Return only changed context.
        
        example: 
        User: Nazywam się James Bond. Mieszkam w Warszawie na ulicy Pięknej 5. Mam 28 lat.
        AI: Nazywam się CENZURA. Mieszkam w CENZURA na ulicy CENZURA. Mam CENZURA lat.
        
        context:
        {data}
        """
        answer = OllamaService().get_completion(prompt=prompt)

        self.verify(answer,"/report")

