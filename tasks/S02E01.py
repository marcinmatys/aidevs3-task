from llmService.openaiService import OpenAIService
from .base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any
from asrService.openaiAsrService import OpenaiASRService

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S02E01(BaseTask):
    def __init__(self):
        super().__init__(base_url,"mp3")

    def run(self) -> Dict[str, Any]:

        # Get the path to the 'resource' directory
        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources/S02E01')

        context = ""
        for filename in os.listdir(resource_dir):
            if not filename.endswith(".m4a"):  # Skip files that are not .m4a
                continue
            file_path = os.path.join(resource_dir, filename)  # Construct full file path
            file= open(file_path, "rb")
            text = OpenaiASRService().get_transcription(file)
            name = os.path.splitext(filename)[0]
            context += f"{name}:\n{text}\n\n"

        prompt = f"""
        Your task is to find university institute location where Andrzej Maj worked, based on below context and your base knowledge.
        
        Rules:
        - In below context you have information about Andrzej Maj from several people.
        - Think out loud(in polish) about your task and steps in the "_thinking" field
         
        Steps:
        - In below context find information about university institute where Andrzej Maj worked.
        - In your base knowledge find university institute location
        - return location street name in street field
        
        Response in json format:
        {{"_thinking":"", street:"street name"}}
        
        context
        ###
        {context}
        ###
        """
        self.logger.info(f"prompt: {prompt}")

        #works also on model="gpt-4o-mini"
        response = OpenAIService().get_completion(prompt, response_format="json_object")
        self.logger.info(f"response: {response}")

        response_json = json.loads(response)
        self.verify(response_json["street"], "/report")