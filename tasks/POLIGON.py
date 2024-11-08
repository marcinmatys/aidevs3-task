from common.HttpUtil import HttpUtil
from .base_task import BaseTask
from typing import Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv('POLIGON_BASE_URL')

class POLIGON(BaseTask):
    def __init__(self):
        super().__init__(base_url,"POLIGON")

    def run(self) -> Dict[str, Any]:

        http_util = HttpUtil(f"{base_url}/dane.txt")

        data = http_util.getData()
        self.logger.info(f"Pobrano dane: {data}")

        self.verify(data.split('\n'))
