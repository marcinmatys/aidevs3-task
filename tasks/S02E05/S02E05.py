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


class S02E05(BaseTask):

    def __init__(self):
        super().__init__(base_url,"arxiv")
        self.questions = None

    def run(self) -> Dict[str, Any]:

        self.questions = self.get_questions()
        self.logger.info(f"questions: {self.questions}")

        publication = self.get_publication_md()

        prompt = self.get_main_prompt(publication)

        try:
            relevant_content = OpenAIService().get_completion(prompt, response_format="json_object")
            relevant_content_json = json.loads(relevant_content)
            pretty_json = json.dumps(relevant_content_json, indent=4, ensure_ascii=False)
            self.logger.info(f"relevant_content: {pretty_json}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

        final_answer = {}
        for question in relevant_content_json['result']:
            answer = ""
            if question['answer']:
                answer = question['answer']

            better_answer = ""
            if question['url'] and question['url'].endswith(".png"):
                better_answer = self.find_answer_from_image(question)
            elif question['url'] and question['url'].endswith(".mp3"):
                better_answer = self.find_answer_from_audio(question)

            if better_answer:
                selected_answer = self.get_better_answer(answer, better_answer, question)

            final_answer[question['questionId']] = selected_answer

        self.logger.info(f"final_answer: {final_answer}")

        self.verify(final_answer, "/report")

    def get_main_prompt(self, publication):
        prompt = f"""
        You have provided fictitious publication in markdown format and questions (both in polish).
        Your task is to find answer or relevant text/url, which can help answer specific questions,
        based only on provided publication.
       
        <rules>
        - Relevant url could be image url or audio url (in format like i/name.png or i/name.mp3)
        - Relevant text/url may be scattered throughout whole publication
        - COMBINING sentences or phrases in relevant text is allowed
        - ADD to text field EVERY publication fragment that could help in response to question
        - ALWAYS ADD markdown link text to related text field ([link text](i/name.png))
        - Information needed for questions could be included in attached image or audio 
        - FILL keywords (important names, phrases) based on text in text_keywords field
        - Find urls based on text and text_keywords
        - UNDER NO CIRCUMSTANCES use same url for different questions
        - Search answer in whole publication and WHEN no clear answer, try to GUESS.
        - WHEN answer for question NOT EXISTS, leave answer field EMPTY
        - WHEN answer is empty, it is MANDATORY to FIND url.
    
        </rules>
        
        <response-format>
        Return relevant elements in json format 
        {{"result":[{{"questionId":"question id","answer":"one sentence answer", "text":"relevant text",
         "text_keywords":"list of keywords","url":"relevant url "}}]}}
        </response-format>
        
        <steps>
        - Read whole publication and questions carefully 
        - Answer questions if possible
        - Find relevant text/url for each question
        - Verify that selected urls are most appropriate for the questions
        - Verify not repeating url across questions
        </steps>
        
        <questions>
        {self.questions}
        </questions>
        
        <publication>
        {publication}
        </publication>
        
        """
        return prompt

    def get_better_answer(self, answer, better_answer, question):
        prompt = f"""
            Your task is to find better answer for question.
            Return the better answer from two offers answer1 and answer2.
            Return only answer.
            
            question: 
            {self.questions[question['questionId']]}
            
            answer1: {answer}\n
            answer2: {better_answer}\n
            
            """
        self.logger.info(f"better answer prompt: {prompt}")
        selected_answer = OpenAIService().get_completion(prompt)
        self.logger.info(f"better answer: {selected_answer}")
        return selected_answer

    def find_answer_from_audio(self, question):

        http_util = HttpUtil(base_url)
        content = http_util.getData(f"/dane/{question['url']}", ResponseType.CONTENT)

        audio = io.BytesIO(content)
        audio.name = question['url'].split("/")[1]
        audio.seek(0)
        text = OpenaiASRService().get_transcription(audio)

        prompt = f"""
            Your task is to find answer the question based on provided text and keywords
            
            question: 
            {self.questions[question['questionId']]}
            
            text: 
            {question['text']}\n\n
            {text}
            
            keywords:
            {question['text_keywords']}
            """
        self.logger.info(f"audio answer prompt: {prompt}")
        response = OpenAIService().get_completion(prompt)
        self.logger.info(f"audio answer response: {question['questionId']}: {response}")
        return response

    def find_answer_from_image(self, question):

        http_util = HttpUtil(base_url)
        content = http_util.getData(f"/dane/{question['url']}", ResponseType.CONTENT)

        image = io.BytesIO(content)
        image_base64 = base64.b64encode(image.read()).decode('utf-8')

        prompt = f"""
            Your task is to find short answer the question based on provided image and context information
            
            question: 
            {self.questions[question['questionId']]}
            
            context: 
            {question['text']}\n
            {question['text_keywords']}
            """
        self.logger.info(f"image answer prompt: {prompt}")
        response = OpenAIVService().get_completion(prompt, [{"base64": image_base64}])
        self.logger.info(f"image answer response: {question['questionId']}: {response}")
        return response


    def get_publication_md(self):

        try:
            script_dir = os.path.dirname(__file__)  # Directory of the script
            resource_dir = os.path.join(script_dir, 'resources')
            file_path = os.path.join(resource_dir, "arxiv.md")

            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()

            http_util = HttpUtil(base_url)
            html = http_util.getData("/dane/arxiv-draft.html")
            prompt = f"""
            Convert provided html to markdown format and return without any additional formatting.
            
            Rules:
            - OMIT resources information
            
            {html}
            """
            markdown = OpenAIService().get_completion(prompt)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(markdown)
            return markdown
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

    def get_questions(self) -> Dict[str,str]:
        http_util = HttpUtil(base_url)
        questions_txt = http_util.getData(f"/data/{api_key}/arxiv.txt")
        # Split the content by lines
        lines = questions_txt.split('\n')
        # Initialize an empty dictionary to hold the split content
        questions_map = {}
        # Iterate over each line
        for line in lines:
            # Split each line by the equals sign
            identifier, question = line.split('=', 1)
            # Add the identifier and question to the dictionary
            questions_map[identifier] = question

        return questions_map
