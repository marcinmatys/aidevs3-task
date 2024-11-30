from llmService.openaiService import OpenAIService
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
import io
import json
from typing import Dict, List, Any
from common.zipUtil import ZipUtil
from common.HttpUtil import HttpUtil, ResponseType
import traceback
import functools
from common.cache import persistent_cache

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S03E01(BaseTask):

    def __init__(self):
        super().__init__(base_url,"dokumenty")
        self.persons = None

    def run(self) -> Dict[str, Any]:

        try:
            http_util = HttpUtil(base_url)
            response = http_util.getData(f"/dane/pliki_z_fabryki.zip", ResponseType.CONTENT)
            files = ZipUtil().extract_to_memory(response)

            self.persons = self.get_persons_info(files)
            #self.logger.info(f"persons: {self.persons}")

            files_keywords = self.get_reports_keywords(files)
            self.logger.info(f"files_keywords: {files_keywords}")

            for report_name in files_keywords:
                name = files_keywords[report_name].split(",")[0]
                name = name.lower()
                self.logger.info(f"name: {name}")

                if not name in self.persons:
                    continue

                person_info = self.persons[name]

                if person_info:
                    self.logger.info(f"person_info founded for: {name}")
                    person_keywords = self.get_keywords(person_info)
                    self.logger.info(f"person_keywords: {person_keywords}")
                    files_keywords[report_name] = files_keywords[report_name] + ", " + person_keywords

            self.verify(files_keywords, "/report")

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    @persistent_cache
    def get_reports_keywords(self, files) -> Dict[str,str]:
        result = {}
        for file_name, content in files.items():
            if not file_name.endswith(".txt") or file_name.startswith("facts/"):
                continue

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            prompt = f"""
            Your task is to find main keywords in below report.
            Return only keywords (in polish) separated with commas without any additional formating.
            
            <rules>
            - Add sector name from report name to keywords
            - SEARCH keywords carefully in report
            - WHEN you find person name in report, return as first keyword
            - Return keywords in denominator
            </rules>
            
            <report>
            report name: {file_name}
            report content: {content}
            </report>
            
            """
            keywords = OpenAIService().get_completion(prompt, temperature=0.5)
            result[file_name] = keywords
            self.logger.info(f"keywords from {file_name}: {keywords}")

        return result

    def get_keywords(self, content):
        prompt = f"""
            Your task is to find main keywords in below context.
            Return only keywords (in polish) separated with commas without any additional formating.
            
            <rules>
            - Return keywords in denominator
            - WHEN you find person name in context, return as first keyword
            </rules>
       
            <context>
            {content}
            </context>
            """
        keywords = OpenAIService().get_completion(prompt)
        return keywords

    def get_persons_info (self, files) -> Dict[str,str]:

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')
        file_path = os.path.join(resource_dir, "persons.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                result = json.load(file)
        else:
            self.logger.info(f"File '{file_path}' does not exist.")
            result = self.prepare_persons_info(files)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(result, file, indent=4, ensure_ascii=False)
        return result

    def prepare_persons_info(self, files) -> Dict[str,str] :

        result = {}
        for file_name, content in files.items():
            if not (file_name.endswith(".txt") and file_name.startswith("facts/")):
                continue

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            if content.startswith("entry deleted"):
                continue

            prompt = f"""
            Your task is to check who is below description about.
            The name of the person is at the beginning of the description.
            Return name surname or only name if surname not exists.
            
            <description>
            {content}
            </description>
            """
            name = OpenAIService().get_completion(prompt)
            result[name.lower()] = content
            self.logger.info(f"name from {file_name}: {name}")

        return result
