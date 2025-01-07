from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
from llmService.openaiService import OpenAIService
import json
from common.HttpUtil import HttpUtil, ResponseType
from flask import Flask, request, jsonify
from common.logger_config import setup_logger

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')


class S04E04(BaseTask):
    def __init__(self):
        super().__init__(base_url,"webhook")

    def run(self) -> Dict[str, Any]:

        self.verify("https://acf6-89-78-216-232.ngrok-free.app/map","/report")

    def map(self, instruction) -> str:
        self.logger.info(f"instruction \n {instruction}")
        return "test"

logger = setup_logger("S04E04")
app = Flask(__name__)
@app.route('/map', methods=['POST'])
def map():
    input_data = request.get_json()
    logger.info(f"input_data \n {input_data}")

    instruction = input_data['instruction']

    prompt = f"""
    Your task is to find element based on the coordinate map and elements placed on the map and provided move instruction.
    
    <rules>
    - You always started in point (0,0)
    - WHEN move right, increase x coordinate
    - WHEN move down, decrease y coordinate
    - Think out loud about your task in "_thinking" field
    - You have provided instruction in polish and return description also in polish
    </rules>
    
    <map>
    Integer coordinates from (0,0) to (3,-3)
    There are elements on individual points:
    (2,0) - drzewo
    (3,0) - budynek
    (1,-1) - wiatrak
    (2,-2),(0,-3),(1,-3) - skały
    (3,-2) - drzewa
    (2,-3) - auto
    (3,-3) - jaskinia
    (other coordinates) - trawa
    </map>
    
    <instruction>
    {instruction}
    <instruction>

    Response in json format {{"_thinking": "", "description":"element name}}    
    Try to simplify instruction before  searching element.
    """

    response = OpenAIService().get_completion(prompt)
    response_json = json.loads(response)
    logger.info(f"response_json \n {response_json}")

    return jsonify(response_json), 200

if __name__ == '__main__':
    app.run(debug=True)
