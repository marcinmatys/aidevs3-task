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
import base64

from visionService.openaiVService import OpenAIVService

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')


class S02E04(BaseTask):

    def __init__(self):
        super().__init__(base_url,"kategorie")

    def run(self) -> Dict[str, Any]:

        daily_reports = self.get_daily_reports()
        pretty_json = json.dumps(daily_reports, indent=4, ensure_ascii=False)
        self.logger.info(f"daily_reports \n {pretty_json}")

        prompt = self.get_prompt(daily_reports)
        #self.logger.info(f"prompt \n {prompt}")

        result = OpenAIService().get_completion(prompt, response_format="json_object")
        result_json = json.loads(result)

        # Sort each array alphabetically
        result_json["people"] = sorted(result_json["people"])
        result_json["hardware"] = sorted(result_json["hardware"])
        self.logger.info(f"result \n {result_json}")

        del result_json['thinking']
        self.verify(result_json,"/report")

    def get_prompt(self, daily_reports):
        prompt = f"""This is an imagined world.
        Machines(Robots) have taken control of the world, and humanity is at risk.
        We (humans) have obtained the daily reports from robots branches that took over the factory.
        Your task is categorize information from reports provided in context.
        
        Rules:
        - Reports are in json format (filename and information fields)
        - categorize as people ONLY WHEN information about captured people or traces of people presence by robots
        - categorize as hardware ONLY WHEN information about fixed hardware faults
        - CRITICAL! Some reports may not fit into any category (watch out for that)
        - Think out loud about your task and categorization for each report in the "_thinking" field
        
        Steps:
        - read reports carefully and think about categorization 
        - decide about categorize or omit
        - make critical checks of categorizations
        - return result in json format
        
        Response json format
        {{ 
        "thinking": "",
        "people": [filenames related to people],
        "hardware": [Filenames related to hardware],
        }}   
        
        <context>
        {daily_reports}
        </context>            
                    
        """
        return prompt

    def get_daily_reports(self):

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')
        file_path = os.path.join(resource_dir, "daily-reports.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                daily_reports = json.load(file)
        else:
            self.logger.info(f"File '{file_path}' does not exist.")
            daily_reports = self.extract_daily_reports()
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(daily_reports, file, indent=4, ensure_ascii=False)
        return daily_reports

    def extract_daily_reports(self):
        http_util = HttpUtil(base_url)
        response = http_util.getData(f"/dane/pliki_z_fabryki.zip", ResponseType.CONTENT)
        files = ZipUtil().extract_to_memory(response)
        audios_info = self.get_audios_info(files)

        images_info = self.get_images_info(files)

        texts_info = self.get_texts_info(files)

        merged_info = audios_info + images_info + texts_info

        return merged_info

    def get_audios_info(self, files) -> List[Dict[str,str]] :
        result = []
        for file_name, content in files.items():
            if not file_name.endswith(".mp3"):
                continue

            audio = io.BytesIO(content)
            audio.name = file_name
            audio.seek(0)
            text = OpenaiASRService().get_transcription(audio)
            item = {"filename":file_name,"information":text}
            result.append(item)
            self.logger.info(f"report {file_name} loaded: {text[:30]}...")
        return result

    def get_images_info(self, files) -> List[Dict[str,str]] :

        result = []
        for file_name, content in files.items():
            if not file_name.endswith(".png"):
                continue

            image = io.BytesIO(content)
            image_base64 = base64.b64encode(image.read()).decode('utf-8')

            prompt = f"""
            Your task is to get main text from provided image and nothing more (no any additional info, header, title, label)
            """
            response = OpenAIVService().get_completion(prompt, [{"base64": image_base64}])
            item = {"filename":file_name,"information":response}
            result.append(item)
            self.logger.info(f"report {file_name} loaded: {response[:30]}...")

        return result

    def get_texts_info(self, files) -> List[Dict[str,str]] :

        result = []
        for file_name, content in files.items():
            if not file_name.endswith(".txt"):
                continue

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            item = {"filename":file_name,"information":content}
            result.append(item)
            self.logger.info(f"report {file_name} loaded: {content[:30]}...")

        return result
