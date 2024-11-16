from llmService.openaiService import OpenAIService
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any
from asrService.openaiAsrService import OpenaiASRService
from .prompt import get_prompt

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S02E01(BaseTask):
    def __init__(self):
        super().__init__(base_url,"mp3")

    def run(self) -> Dict[str, Any]:

        # Get the path to the 'resource' directory
        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        transcription = self.get_summary_transcription(resource_dir)

        prompt = get_prompt(transcription)
        self.logger.info(f"prompt: {prompt}")

        #works also on model="gpt-4o-mini"
        response = OpenAIService().get_completion(prompt, response_format="json_object")
        self.logger.info(f"response: {response}")

        response_json = json.loads(response)
        self.verify(response_json["street"], "/report")

    def get_summary_transcription(self, resource_dir):
        result = ""
        for filename in os.listdir(resource_dir):
            if not filename.endswith(".m4a"):  # Skip files that are not .m4a
                continue
            file_path = os.path.join(resource_dir, filename)  # Construct full file path
            file = open(file_path, "rb")
            text = OpenaiASRService().get_transcription(file)
            name = os.path.splitext(filename)[0]
            result += f"{name}:\n{text}\n\n"
        return result