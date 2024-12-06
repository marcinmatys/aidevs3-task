from common.HttpUtil import HttpUtil
from llmService.openaiService import OpenAIService
from .base_task import BaseTask
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Any

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S03E03(BaseTask):
    def __init__(self):
        super().__init__(base_url,"database")

    def run(self) -> Dict[str, Any]:

        #show tables
        #{'reply': [{'Tables_in_banan': 'connections'}, {'Tables_in_banan': 'correct_order'}, {'Tables_in_banan': 'datacenters'},
        #{'Tables_in_banan': 'users'}], 'error': 'OK'}

        datacenter_table = self.get_table_definition("datacenters")
        users_table = self.get_table_definition("users")

        question = "które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)"

        # We can also add this to prompt
        # Create query to get active datacenters (dc_id) managed by not active users (users_table).

        prompt = f"""
        Your task is to create sql query for MySQL database based on provided DB Model and question.
        Create sql query to get response for provided question.
     
        Response in json format {{"sql":"sql query"}}
        
        DB Model:
        {datacenter_table}\n\n
        {users_table}
        
        Question:
        {question}
        """
        self.logger.info(f"prompt:  {prompt}")

        response = OpenAIService().get_completion(prompt, temperature=0.5, response_format="json_object")
        response_json = json.loads(response)
        sql = response_json['sql']
        self.logger.info(f"sql:  {sql}")

        sql_result = self.get_sql_result(sql)

        dcids = [dc['dc_id'] for dc in sql_result['reply']]

        self.verify(dcids, "/report")

    def get_sql_result(self, sql):
        http_util = HttpUtil(base_url)

        params = {
            "task": "database",
            "apikey": api_key,
            "query": sql
        }
        sql_result = http_util.sendData(params, "apidb")
        self.logger.info(f"sql_result:  {sql_result}")
        return sql_result

    def get_table_definition(self, table):

        http_util = HttpUtil(base_url)

        params = {
            "task": "database",
            "apikey": api_key,
            "query": f"show create table {table}"
        }
        data = http_util.sendData(params, "apidb")
        table = data['reply'][0]['Create Table']
        self.logger.info(f"{table} table \n {table}")
        return table


