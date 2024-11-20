from common.HttpUtil import HttpUtil
from imagegenService.openaiImageService import OpenAIImageService
from .base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S02E03(BaseTask):
    def __init__(self):
        super().__init__(base_url,"robotid")

    def run(self) -> Dict[str, Any]:

        http_util = HttpUtil(base_url)

        data = http_util.getData(f"/data/{api_key}/robotid.json")
        self.logger.info(f"data \n {data}")

        data_json = json.loads(data)

        prompt = data_json['description']
        self.logger.info(f"prompt \n {prompt}")

        url = OpenAIImageService().generate(prompt=prompt)
        self.logger.info(f"url \n {url}")

        self.verify(url,"/report")

