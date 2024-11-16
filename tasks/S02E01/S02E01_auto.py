from llmService.openaiService import OpenAIService
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
import io
from io import BytesIO
import json
from typing import Dict, List, Any
from asrService.openaiAsrService import OpenaiASRService
from common.zipUtil import ZipUtil
from common.HttpUtil import HttpUtil, ResponseType
from .prompt import get_prompt

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S02E01_auto(BaseTask):
    def __init__(self):
        super().__init__(base_url,"mp3")

    def run(self) -> Dict[str, Any]:

        http_util = HttpUtil(base_url)
        response = http_util.getData(f"/dane/przesluchania.zip", ResponseType.CONTENT)

        files = ZipUtil().extract_to_memory(response)

        transcription = self.get_summary_transcription(files)

        prompt = get_prompt(transcription)
        self.logger.info(f"prompt: {prompt}")

        #works also on model="gpt-4o-mini"
        response = OpenAIService().get_completion(prompt, response_format="json_object")
        self.logger.info(f"response: {response}")

        response_json = json.loads(response)
        self.verify(response_json["street"], "/report")

    def get_summary_transcription(self, files):
        result = ""
        for file_name, content in files.items():
            audio = io.BytesIO(content)
            audio.name = file_name
            audio.seek(0)
            text = OpenaiASRService().get_transcription(audio)
            name = os.path.splitext(file_name)[0]
            result += f"{name}:\n{text}\n\n"
        return result