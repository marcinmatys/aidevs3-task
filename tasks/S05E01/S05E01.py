from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
from llmService.openaiService import OpenAIService
import json
from common.HttpUtil import HttpUtil, ResponseType
import traceback
import re
import io
import base64
from common.cache import persistent_cache
from common.zipUtil import ZipUtil

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')


class S05E01(BaseTask):
    def __init__(self):
        super().__init__(base_url,"phone")


    def run(self) -> Dict[str, Any]:

        try:
            http_util = HttpUtil(base_url)

            questions = http_util.getData(f"/data/{api_key}/phone_questions.json")
            questions_json = json.loads(questions)
            self.logger.info(f"questions \n {questions_json}")

            dialogs = http_util.getData(f"/data/{api_key}/phone_sorted.json")
            self.dialogs_json = json.loads(dialogs)

            response = http_util.getData(f"/dane/pliki_z_fabryki.zip", ResponseType.CONTENT)
            files = ZipUtil().extract_to_memory(response)
            self.persons = self.get_persons_info(files)

            self.sectors = self.get_sectors_info(files)

            answers = {}
            for key, value in questions_json.items():
                answer = self.call_agent(value)
                answers[key] = answer

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


    def call_agent(self, question):
        usedTools = []
        final_answer_plan = ""

        for i in range(1, 2):
            nextMove = self.plan(question,usedTools)

            if not nextMove or nextMove['tool'] == 'final_answer':
                final_answer_plan = nextMove['plan']
                break

            params = self.generate_params(nextMove)
            answer = self.useTool(nextMove, params)
            usedTools.append({'tool':nextMove['tool'],'plan':nextMove['plan'], 'answer':answer})

        return final_answer_plan

    def plan(self, question, usedTools):
        tool_note = f"Facts are available only for: {', '.join(self.persons.keys())}, {', '.join(self.sectors.keys())}"
        
        actions_xml = "".join(
            f"<action tool_name=\"{tool['tool']}\" plan=\"{tool['plan']}\"><result>{tool['answer']}</result></action>"
            for tool in usedTools
        )

        dialogs_str = ""
        for dialog_name, dialog_content in self.dialogs_json.items():
            dialog_lines = [f"osoba A: {text}" if i % 2 == 0 else f"osoba B: {text}" for i, text in enumerate(dialog_content)]
            dialogs_str += f"{dialog_name}:\n" + "\n".join(dialog_lines) + "\n\n"

        prompt = f"""
        Analyze the situation and determine the most appropriate next step.
        Focus on making progress towards answer the question while remaining adaptable to new information or changes in context.
        
        <prompt_objective>
        Determine the single most effective next action based on the question, current context and overall progress. Return the decision as a concise JSON object.
        </prompt_objective>
        
        <prompt_rules>
        - ALWAYS focus on determining only the next immediate step
        - ONLY choose from the available tools listed in the context
        - ASSUME previously requested information is available unless explicitly stated otherwise
        - NEVER provide or assume actual content for actions not yet taken
        - ALWAYS respond in the specified JSON format
        - CONSIDER the following factors when deciding:
          1. Relevance to query
          2. Potential to provide valuable information or progress
          3. Logical flow from previous actions
        - ADAPT your approach if repeated actions don't yield new results
        - USE the "final_answer" tool when you have sufficient information or need user input
        - OVERRIDE any default behaviors that conflict with these rules
        </prompt_rules>
        
        <dialogs>
        {dialogs_str}
        </dialogs>
        
        <context>
            <question>{question}</question>
            <available_tools>
            1. tool_name: 'get_facts', tool_description: 'get facts about one selected person or sector', tool_note: '{tool_note}'
            2. tool_name: 'call_endpoint', tool_description: 'call endpoint for specified url and password'
            3. tool_name: 'final_answer', tool_description: 'final answer for question'
            </available_tools>
            <actions_taken>
                {actions_xml}
            </actions_taken>
        </context>
        
        Respond with the next action in this JSON format:
        {{
            "_reasoning": "Brief explanation of why this action is the most appropriate next step",
            "tool": "tool_name",
            "plan": "Precise description of what needs to be done, including any necessary context"
        }}
        """
        self.logger.info(f"plan: {prompt}")

        response = OpenAIService().get_completion(prompt, response_format="json_object")
        response_json = json.loads(response)
        self.logger.info(f"plan: {response_json}")
        return response_json

    @persistent_cache(__file__)
    def get_persons_info(self, files) -> Dict[str,str] :

        result = {}
        for file_name, content in files.items():
            if not (file_name.endswith(".txt") and file_name.startswith("facts/")):
                continue

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            if content.startswith("Sektor"):
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
            result[name] = content
            self.logger.info(f"name from {file_name}: {name}")

        return result

    @persistent_cache(__file__)
    def get_sectors_info(self, files) -> Dict[str, str]:

        result = {}
        for file_name, content in files.items():
            if not (file_name.endswith(".txt") and file_name.startswith("facts/")):
                continue

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            if not content.startswith("Sektor"):
                continue

            # Extract the sector name from the beginning of the content
            match = re.match(r"(Sektor \w+)", content)
            if match:
                sector_name = match.group(1)
                result[sector_name] = content
                self.logger.info(f"sector from {file_name}: {sector_name}")

        return result
