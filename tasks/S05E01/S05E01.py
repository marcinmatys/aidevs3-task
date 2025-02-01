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

            self.tools = self.getToolsDescr()

            answers = {}
            questions_json = dict(list(questions_json.items())[:1])
            self.logger.info(f"questions \n {questions_json}")
            for key, value in questions_json.items():
                answer = self.call_agent(value)
                answers[key] = answer

            self.logger.info(f"answers: {answers}")

            self.verify(answers,"/report")
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


    def call_agent(self, question):
        usedTools = []
        final_answer_plan = ""

        for i in range(1, 4):
            nextMove = self.plan(question,usedTools)

            if not nextMove or nextMove['tool'] == 'final_answer':
                final_answer_plan = nextMove['plan']
                break

            params = self.generate_params2(nextMove)
            answer = self.useTool(nextMove, params)
            #self.logger.info(f"answer from tool: {answer}")
            usedTools.append({'tool':nextMove['tool'],'plan':nextMove['plan'], 'answer':answer})
            #self.logger.info(f"usedTools: {usedTools}")

        return final_answer_plan

    def plan(self, question, usedTools):
        tool_note = f"Facts are available only for: {', '.join(self.persons.keys())}, {', '.join(self.sectors.keys())}"
        tool_note = f"{', '.join(self.persons.keys())}, {', '.join(self.sectors.keys())}"
        
        actions_xml = "".join(
            f"<action tool_name=\"{tool['tool']}\" plan=\"{tool['plan']}\"><result>{tool['answer']}</result></action>"
            for tool in usedTools
        )
        self.logger.info(f"actions_xml: {actions_xml[:200]}")

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
        - USE the "final_answer" tool when you have sufficient information
        - NEVER call get_facts tool for person or sector outside available list
        - OVERRIDE any default behaviors that conflict with these rules
        </prompt_rules>
        
        <dialogs>
        {dialogs_str}
        </dialogs>
        
        <context>
            <question>{question}</question>
            <available_tools>
            1. tool_name: 'get_facts', tool_description: 'use to retrieves facts for only one specified person or sector from the available list: {tool_note}'
            2. tool_name: 'call_endpoint', tool_description: 'use to call endpoint for specified url and password'
            3. tool_name: 'final_answer', tool_description: 'use only when you know final answer for question'
            </available_tools>
            <actions_taken>
                {actions_xml}
            </actions_taken>
        </context>
        
        Respond with the next action in this JSON format:
        {{
            "_reasoning": "Brief explanation of why this action is the most appropriate next step",
            "tool": "tool_name",
            "plan": "Precise description of what needs to be done, including necessary data for using tool"
        }}
        """
        #self.logger.info(f"plan: {prompt}")

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

    def generate_params(self, nextMove):

        if(nextMove['tool'] == "get_facts"):
            result = self.generate_params_facts(nextMove)
        elif (nextMove['tool'] == "call_endpoint"):
            result = self.generate_params_endpoint(nextMove)
        else:
            self.logger.error(f"tool {nextMove['tool']} not found!")
            raise

        return result

    def generate_params2(self, nextMove):

        tool = self.tools[nextMove['tool']]

        prompt = f"""
        Your task is to extract params needed to execute the tool based on agent plan description.
        
        <plan>
        {nextMove['plan']}
        <plan>
        
        <tool>
        tool name: {nextMove['tool']}
        tool description: {self.tools[nextMove['tool']]['description']} 
        </tool>
        
        Response in json format
        {tool['params']}
        """
        self.logger.info(f"generate_params_facts prompt: {prompt}")
        response = OpenAIService().get_completion(prompt, response_format="json_object")
        response_json = json.loads(response)
        self.logger.info(f"generate_params_facts response: {response_json}")
        return response_json

    def getToolsDescr(self):

        get_facts_note = f"Facts are available only for: {', '.join(self.persons.keys())}, {', '.join(self.sectors.keys())}"

        tools = {
            'get_facts':{
                'description':'get facts about one selected person or sector',
                'note': get_facts_note,
                'params':{
                    'person_name':'simple name of the person',
                    'sector_name':'simple sector name like "Sektor X"'
                }
            },
            'call_endpoint':{
                'description':'call endpoint for specified url and password',
                'note': '',
                'params':{
                    'url':'endpoint url',
                    'password':'password'
                }
            }

        }

        return tools

    def useTool(self, nextMove, params):

        method = getattr(self, nextMove['tool'], None)

        # Check if the method exists and is callable
        if callable(method):
            return method(**params)  # Unpacking dictionary as keyword arguments
        else:
            self.logger.error(f"Method '{nextMove['tool']}' not found.")
            raise

    def get_facts(self,person_name, sector_name):
        self.logger.error(f"getting facts for {person_name} {sector_name}")
        if person_name:
            return self.persons[person_name] #return "Brak inforamcji" when  person_name not in self.persons AI!

        if sector_name:
            return self.sectors[sector_name]

    def call_endpoint(self,url, password):
        http_util = HttpUtil(url)
        response = http_util.sendData({'password':password})
        self.logger.info(f"endpoint response : {response}")

        return response['message']