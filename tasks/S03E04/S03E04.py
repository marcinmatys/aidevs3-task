from common.HttpUtil import HttpUtil
from llmService.openaiService import OpenAIService
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any
import traceback

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S03E04(BaseTask):
    def __init__(self):
        super().__init__(base_url,"loop")


    def run(self) -> Dict[str, Any]:

        try:
            http_util = HttpUtil(base_url)

            note = http_util.getData("/dane/barbara.txt")
            self.logger.info(f"note:  {note}")

            place = self.get_result(note)
            response = self.verify(place,"/report")
            self.logger.info(f" verify response:  {response}")


        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    def get_result(self, note):

        http_util = HttpUtil(base_url)

        result = None
        history = ""
        for i in range(10):
            self.logger.info(f"process {i}...")

            prompt = self.get_prompt(history, note)
            self.logger.info(f"after get_prompt")
            response = OpenAIService().get_completion(prompt, response_format="json_object")
            self.logger.info(f"after get_completion")
            response_json = json.loads(response)
            self.logger.info(f"response:  {response_json}")

            if 'tool' in response_json and response_json['tool'] == "people":
                params = {
                    "apikey": api_key,
                    "query": response_json['name']
                }
                people_response = http_util.sendData(params, "people")
                self.logger.info(f"people_response:  {people_response['message']}")
                history += f"tool people result for name {response_json['name']}: {people_response['message']}\n"
            elif 'tool' in response_json and response_json['tool'] == "places":
                params = {
                    "apikey": api_key,
                    "query": response_json['name']
                }
                places_response = http_util.sendData(params, "places")
                self.logger.info(f"places_response:  {places_response['message']}")
                history += f"tool places result for name {response_json['name']}: {places_response['message']}\n"
            elif 'place' in response_json:
                result = response_json['place']
                break
            else:
                self.logger.info(f"unexpected response:  {response_json}")
                break
        return result

    def get_prompt(self, history, note):

        self.logger.info(f"prompt history:\n{history}")

        prompt = f"""
            You are a detective and your task is to find Barbara's current place.
            You have a note provided about Barbara as a start point.
            
            IF you don't know barbara's place, use one of below tool:
            1. "people" tool - enter a person name in nominative case to search for places where that person was spotted.
            If you want to use this tool, return json {{"_thinking":"", "tool":"people", "name":"people FIRST NAME (uppercase)"}}
            2. "places" tool - enter place name in nominative case to search for peoples seen there
            If you want to use this tool, return json {{"_thinking":"", "tool":"places", "name":"PLACE NAME (uppercase)"}}
            
            IF you know Barbara place, just return json {{"_thinking":"", "place":"Barbara's PLACE (uppercase) in nominative without diacritics"}}
        
            <rules>
            - You have using-tools-history provided, where you can see whole history of using tools.
            - NEVER use tool for specific name again (check using-tools-history).
            - ALWAYS put name for tool in polish WITHOUT diacritics and polish letters (e.g RAFAL or KRAKOW)
            - IF you do not know Barbara place, use one of tool
            - WHEN use tool, ALWAYS put ONE WORD in name field
            - Tool history is initially empty and will be filled in subsequent iterations
            - NEVER use tool "people" for person name "Barbara"
            - "places" tool returns information about people were seen in this location, not their current stay
            - WHEN "places" tool return [**RESTRICTED DATA**], means you can't get information about peoples for this place.
            - MEAN place always as city
            - WHEN use tool, ALWAYS search name in note or tools history
            - Think out loud about your task in "_thinking" field
            </rules>
            
            <note>
            {note}
            </note>
            
            <using-tools-history>
            {history}
            <using-tools-history>
            
            Find Barbara's current place based on using-tools-history.
            Use available tools IF you need. Follow above rules.
            Answer below questions could be helpful to identify the next place where it is worth looking for Barbara
            
            <questions>
            Who was Aleksander and Barbara's collaborator?
            Who did Rafał meet with? 
            </questions>
            
            """
        return prompt


