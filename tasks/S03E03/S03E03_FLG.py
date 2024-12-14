from common.HttpUtil import HttpUtil
from llmService.openaiService import OpenAIService
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
import traceback

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S03E03_FLG(BaseTask):
    def __init__(self):
        super().__init__(base_url,"database")

    def run(self) -> Dict[str, Any]:


        try:
            sql_result = self.get_sql_result("select letter from correct_order order by weight")

            result = ''.join(item['letter'] for item in sql_result['reply'])
            self.logger.info(f"result:  {result}")
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


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
