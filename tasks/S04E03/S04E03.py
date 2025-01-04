from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
import traceback
from llmService.openaiService import OpenAIService
import json
from common.HttpUtil import HttpUtil, ResponseType
from markitdown import MarkItDown

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')



class S04E03(BaseTask):
    def __init__(self):
        super().__init__(base_url,"softo")

    def run2(self) -> Dict[str, Any]:

        md = MarkItDown()
        result = md.convert("https://softo.ag3nts.org/blog", extension="html")
        self.logger.info(f"result \n {result.text_content}")

    def run(self) -> Dict[str, Any]:

        try:

            http_util = HttpUtil(base_url)

            questions = http_util.getData(f"/data/{api_key}/softo.json")
            questions_json = json.loads(questions)
            self.logger.info(f"questions \n {questions_json}")

            answers = {}
            for key, value in questions_json.items():

                answers[key] = self.find_answer(value)

            self.logger.info(f"answers \n {answers}")

            self.verify(answers,"/report")

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    def find_answer(self, question):
        answer_founded = False
        search_count = 0

        link = ""
        answer = ""
        while not answer_founded and search_count < 4:
            site_md = self.get_site_md(link)
            answer = self.find_answer_llm(question, site_md)
            if not answer:
                link = self.find_link(question, site_md)
                if not link:
                    break
            else:
                answer_founded = True

            search_count = search_count + 1

        return answer

    def get_site_md(self, link):
        base_url = "https://softo.ag3nts.org"

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        filename = link if link else "main"
        filename = filename.replace("/", "_")
        file_path = os.path.join(resource_dir, filename+".md")
        file_md = None
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                file_md = file.read()

        if not file_md:
            file_md = self.html_to_markdown(f"{base_url}/{link}")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(file_md)

        return file_md

    def html_to_markdown(self, url):
        self.logger.info(f"html_to_markdown for: {url}")
        md = MarkItDown()
        result = md.convert(url)
        return result.text_content

    def find_answer_llm(self, question, context):
        prompt = f"""
        Your task is to find short,concise answer for provided question in below context.
        If there is no answer, just return NO_ANSWER string and nothing more.
        Response always in Polish.
        
        Question:
        {question}
        
        Context:
        {context}
        """

        response = OpenAIService().get_completion(prompt=prompt)
        self.logger.info(f"find_answer_llm question: {question}")
        self.logger.info(f"find_answer_llm response: {response}")

        return "" if response == "NO_ANSWER" else response

    def find_link(self, question, context):

        prompt = f"""
        Your task is to find the best link or url in below context to search answer for provided question.
        Find link or url that has the highest probability of finding the answer.

        Rules:
        - in context there is content in markdown format
        - ALWAYS get link from parentheses according to markdown syntax
        - return only link like /link or full url starting with https://
        - NEVER add any additional formating or information
        
        
        Question:
        {question}
        
        Context:
        {context}
        """

        response = OpenAIService().get_completion(prompt=prompt)
        self.logger.info(f"founded link/url:{response}")

        link = "" if response == "NO_LINK" else response.strip()

        if link.startswith("http"):
            link = link.rsplit('/', 1)[-1]

        link = link.strip("/")
        self.logger.info(f"founded link:{link}")

        return link







