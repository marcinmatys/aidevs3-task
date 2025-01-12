from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
from llmService.openaiService import OpenAIService
import json
from common.HttpUtil import HttpUtil, ResponseType
import traceback
from markitdown import MarkItDown
import re
import io
import base64
from visionService.openaiVService import OpenAIVService
from common.cache import persistent_cache

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')


class S04E05(BaseTask):
    def __init__(self):
        super().__init__(base_url,"notes")

    def run2(self) -> Dict[str, Any]:

        last_site_text = self.get_last_site()
        self.logger.info(f"before correction: \n {last_site_text}")
        last_site_text = self.correct_last_site(last_site_text)
        self.logger.info(f"after correction:  \n {last_site_text}")


    def run(self) -> Dict[str, Any]:

        try:

            http_util = HttpUtil(base_url)

            questions = http_util.getData(f"/data/{api_key}/notes.json")
            questions_json = self.clean_text(json.loads(questions))
            self.logger.info(f"questions \n {questions_json}")

            notes_md = self.get_notes_md()
            last_site_text = self.get_last_site()
            last_site_text = self.correct_last_site(last_site_text)
            place_descr = self.get_place_descr()

            notes = self.save_full_notes(notes_md,last_site_text, place_descr)

            notes = self.organize_notes(notes)

            answers = {}
            for key, value in questions_json.items():

                #answers[key] = self.find_answer(value, notes)
                answers[key] = "test"

            self.logger.info(f"answers \n {answers}")

            for i in range(1, 6):
                index = f"0{i}"
                answers[index] = self.find_answer(questions_json[index], notes)
                response = self.verify(answers,"/report")

                search_count = 0;
                forbidden = ""
                while not self.answer_founded(response, index) and search_count < 4:
                    #forbidden  = f"{forbidden}\n{questions_json[index]}: {answers[index]}"
                    forbidden  = f"{forbidden}\n{answers[index]}"
                    answers[index] = self.find_answer(questions_json[index], notes, forbidden)
                    response = self.verify(answers,"/report")
                    search_count = search_count + 1

                if self.answer_founded(response, index):
                    self.logger.info(f"answers founded for {index}: {answers[index]}")
                else:
                    break

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    def get_notes_md(self):

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        file_path = os.path.join(resource_dir, "notes.md")
        file_md = None
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                file_md = file.read()

        if not file_md:
            file_md = self.to_markdown(f"{base_url}/dane/notatnik-rafala.pdf")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(file_md)

        return file_md

    def to_markdown(self, url):
        self.logger.info(f"to_markdown for: {url}")
        md = MarkItDown()
        result = md.convert(url)
        return result.text_content

    def find_answer(self, question, notes, forbidden_answers = ""):
        prompt = f"""
        Your task is to find short, concise answer for provided question based on below context and your base knowledge.
        In context you have notes of a fictional person Rafał, who moved from the future to the past using time machine.
        
        Rules:
        - IF answer is not directly in text, try to deduce it using context and base knowledge
        - Include all the facts provided in the text, particularly references to events
        - CRITICAL!: UNDER NO CIRCUMSTANCES respond with forbidden answers, necessarily find another answer
        - For question about year, return only year and nothing more
        - KEEP in mind that Rafał could refers to dates relatively and does not mention it literally. Verify how Rafal talks about time and in relation to which date.
          Tomorrow is the next day, not day before. 
        - Notes may contain errors in place name so search place with similar name in your base knowledge 
        - Response always in Polish
        
        Response in json format {{"_thinking": "", "answer":"answer"}}
        Think out loud about your task in "_thinking" field
        
        <question>
        {question}
        </question>
        
        <forbidden-answers>
        {forbidden_answers}
        <forbidden-answers>
        
        <context>
        {notes}
        </context>
        
        Find your best answer considering all instructions. NEVER response with forbidden answers!
        """

        self.logger.info(f"forbidden_answers: {forbidden_answers}")
        response = OpenAIService().get_completion(prompt=prompt, response_format="json_object")
        response_json = json.loads(response)
        self.logger.info(f"find_answer question: {question}")
        self.logger.info(f"find_answer response: {response_json}")

        return response_json['answer']

    def get_last_site(self):
        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        file_path = os.path.join(resource_dir, "last_site.md")
        file_md = None
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                file_md = file.read()

        return file_md

    def clean_text(self,data):
        if isinstance(data, dict):
            return {key: self.clean_text(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.clean_text(element) for element in data]
        elif isinstance(data, str):
            return data.replace("\xa0", " ")  # Replace with space
        return data

    def organize_notes(self, notes):

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        file_path = os.path.join(resource_dir, "organized_notes.md")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()

        prompt = f"""
        Your task is to proofread and organize notes.
        You have provided notes of a fictional person name Rafał, who moved from the future to the past using time machine.
        Try to organize information to make it clear what happened in sequence.
        Divide information into separate sections .
        
        Rules:
        - Correct place names if has mistake or typos
        - KEEP all content, do not delete anything.
        - Return only corrected notes in Polish.
        
        <notes>
        {notes}
        </notes>
        
        Organize notes into sections. keep all content, all information is important.

        """

        self.logger.info(f"organize...")
        response = OpenAIService().get_completion(prompt=prompt)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(response)

        return response

    def answer_founded(self, response, index):
        message = response['message']
        match = re.search(r'question (\d{2})', message)

        question_no = ""
        if match:
            question_no = match.group(1)  # Group 1 contains only the digits after "question"
        else:
            self.logger.info(f"question_no not found")

        self.logger.info(f"index: {index}, question_no: {question_no}")
        return not (index == question_no and response['code'] == -340)

    @persistent_cache(__file__)
    def get_place_descr(self):

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        file_path = os.path.join(resource_dir, "place.png")
        content = None
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                content = file.read()

        image_base64 = base64.b64encode(content).decode('utf-8')

        prompt = f"""
            Your task is find place on provided image.
            Return short place description with place name.
            Return only description in Polish and nothing more.
            """
        response = OpenAIVService().get_completion(prompt, [{"base64": image_base64}])
        self.logger.info(f"place description: {response}")
        return response

    #@persistent_cache(__file__)
    def get_last_site2(self):

       script_dir = os.path.dirname(__file__)  # Directory of the script
       resource_dir = os.path.join(script_dir, 'resources')

       file_path = os.path.join(resource_dir, "last_site.png")
       content = None
       if os.path.exists(file_path):
           with open(file_path, "rb") as file:
               content = file.read()

       image_base64 = base64.b64encode(content).decode('utf-8')

       prompt = f"""
               Your task is to get all text from provided image.
               Return only text in Polish and nothing more.
               """
       self.logger.info(f"getting last site description...")
       response = OpenAIVService().get_completion(prompt, [{"base64": image_base64}])
       #self.logger.info(f"place description: {response}")
       return response

    def save_full_notes(self, notes, last_site, place_descr):
        result = f"{notes}\n\n{last_site}\n\n{place_descr}"

        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        file_path = os.path.join(resource_dir, "full_notes.md")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(result)

        return result

    @persistent_cache(__file__)
    def correct_last_site(self, text):
        prompt = f"""
        Your task is to proofread provided text.
        Look at Polish place names and correct if has mistake or typos.
        Analyze whole text to find correct place name.
        Return only corrected text in Polish.
        
        <text>
        {text}
        </text>

        """

        self.logger.info(f"correcting last site...")
        response = OpenAIService().get_completion(prompt=prompt)
        return response



