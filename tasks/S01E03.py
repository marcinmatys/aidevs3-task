from common.HttpUtil import HttpUtil
from common.logger_config import setup_logger
from llmService.openaiService import OpenAIService
from .base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S01E03(BaseTask):
    def __init__(self):
        super().__init__(base_url,"JSON")

    def run(self) -> Dict[str, Any]:

        http_util = HttpUtil(base_url)

        data = http_util.getData(f"/data/{api_key}/json.txt")
        # Parse input JSON
        input_json = json.loads(data)
        processor = JsonProcessor(input_json)
        questions = processor.extract_test_questions()

        self.logger.info(f"questions \n {questions}")

        prompt = self.prepare_prompt(questions)

        answers = OpenAIService().get_completion(prompt=prompt, response_format="json_object")
        self.logger.info(f"answers \n {answers}")

        answers_json = json.loads(answers)
        processor.update_answers(answers_json["result"])

        input_json["apikey"] = api_key

        self.verify(input_json,"/report", False)

    def prepare_prompt(self, questions):
        prompt = f"""
        Fill answers(a) for questions(q) in input json and return this json in format:
        {{"result": [{{"q": "question', "a": "answer"}}]}}
        
        ###
        input json
        ###
        {questions}
        ###
        
        Rules
        ###
        - Give short answer without additional explanation
        ###
        """
        self.logger.info(f"Prompt \n {prompt}")
        return prompt


class JsonProcessor:
    def __init__(self, input_json: Dict[str, Any]):
        self.input_json = input_json
        self.test_data = input_json.get('test-data', [])
        self.logger = setup_logger(self.__class__.__name__)

        self.correct_calculations()

    def extract_test_questions(self) -> List[Dict[str, str]]:
        """Extract test questions from the input JSON."""
        test_questions = []

        for item in self.test_data:
            if 'test' in item:
                test_questions.append({
                    'q': item['test']['q'],
                    'a': item['test']['a']
                })

        return test_questions

    def update_answers(self, answered_questions: List[Dict[str, str]]) -> None:
        """Update the original JSON with answered questions."""
        # Create a mapping of questions to answers
        answer_map = {q['q']: q['a'] for q in answered_questions}

        # Update the original JSON
        for item in self.test_data:
            if 'test' in item and item['test']['q'] in answer_map:
                item['test']['a'] = answer_map[item['test']['q']]


    def correct_calculations(self):
        for item in self.test_data:
            # Extract the question string
            question = item['question'].strip()

            # Extract numbers from the question
            numbers = [int(num.strip()) for num in question.split('+')]

            # Calculate the correct sum
            correct_sum = sum(numbers)

            # Get the provided answer
            provided_answer = int(item['answer'])

            if provided_answer != correct_sum :
                self.logger.info(f"incorrect {item['question']} = {item['answer']} changed to {correct_sum}")
                item['answer'] = correct_sum



