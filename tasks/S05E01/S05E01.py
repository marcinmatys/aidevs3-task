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

        for i in range(1, 6):
            nextMove = self.plan(question,usedTools)

            if not nextMove or nextMove['tool'] == 'final_answer':
                final_answer_plan = nextMove['plan']
                break

            params = self.generate_params(nextMove)
            answer = self.useTool(nextMove, params)
            usedTools.append({'tool':nextMove['tool'],'plan':nextMove['plan'], 'answer':answer})

        return final_answer_plan

    def plan(self, question, usedTools):
        actions_xml = "".join(
            f"<action><tool>{tool['tool']}</tool><plan>{tool['plan']}</plan><answer>{tool['answer']}</answer></action>"
            for tool in usedTools
        )
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
        
        <context>
            <question>{question}</question>
            <available_tools>
            1. tool_name: 'get_facts', tool_description: 'get facts about person or sector', tool_note: 'Facts are available only for: {facts_note}'
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
