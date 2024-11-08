from common.HttpUtil import HttpUtil
from .base_task import BaseTask
from typing import Dict, Any
from llmService.openaiService import OpenAIService
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv('XYZ_BASE_URL')


class S01E01(BaseTask):
    def run(self) -> Dict[str, Any]:

        http_util = HttpUtil(base_url)

        data = http_util.getData()
        self.logger.info(f"Form \n {data}")

        question_text = self.get_human_question(data)

        prompt = f"""
        Return very short answer the question in below context. Only short answer and nothing more.
        
        context
        ###
        {question_text}
        ###"""

        answer = OpenAIService().get_completion(prompt=prompt, model="gpt-4o-mini")
        self.logger.info(f"Answer \n {answer}")

        data = f"username=tester&password=574e112a&answer={answer}"

        html = http_util.sendForm(data)
        self.logger.info(f"HTML \n {html}")

        readable_html = OpenAIService().get_completion(prompt=f"Convert html to markdown and return only markdown.\nhtml###{html}###", model="gpt-4o")
        self.logger.info(f"Answer \n {readable_html}")



    def get_human_question(self, html_content: str) -> str:
        """Extracts the human question from the HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        question_element = soup.find(id="human-question")
        if question_element:
            question_text = question_element.get_text(strip=True).replace("Question:", "").strip()
            self.logger.info(f"Human Question: {question_text}")
            return question_text
        else:
            self.logger.info("Human question not found")
            return ""
