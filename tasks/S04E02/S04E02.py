from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
import traceback
from llmService.openaiService import OpenAIService
import json
from common.HttpUtil import HttpUtil, ResponseType
from common.zipUtil import ZipUtil

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')
ft_model = os.getenv('FT_MODEL')


class S04E02(BaseTask):
    def __init__(self):
        super().__init__(base_url,"research")

    def run(self) -> Dict[str, Any]:
        content_to_verify = self.get_content_to_verify()
        self.logger.info(f"content_to_verify:  {content_to_verify}")

        lines = content_to_verify.strip().split("\n")
        self.logger.info(f"lines:  {len(lines)}")

        valid_data_ids = []
        for line in lines:
            line_splited = line.split("=")
            id = line_splited[0]
            data = line_splited[1]

            prompt = f"""verify data correctness: {data}"""
            self.logger.info(f"prompt:  {prompt}")
            response = OpenAIService().get_completion(prompt, model= ft_model)
            self.logger.info(f"response:  {response}\n\n")

            if response.strip() == "1":
                valid_data_ids.append(id)

        self.logger.info(f"valid_data_ids:  {valid_data_ids}")

        self.verify(valid_data_ids,"/report")



    def get_content_to_verify(self):

        http_util = HttpUtil(base_url)
        response = http_util.getData(f"/dane/lab_data.zip", ResponseType.CONTENT)
        files = ZipUtil().extract_to_memory(response)

        for file_name, content in files.items():
            if not file_name == "verify.txt":
                continue

            if isinstance(content, bytes):
                return  content.decode('utf-8')


