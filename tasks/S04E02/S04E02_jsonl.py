from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
import json
from common.HttpUtil import HttpUtil, ResponseType
from common.zipUtil import ZipUtil

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')


class S04E02_jsonl(BaseTask):
    def __init__(self):
        super().__init__(base_url,"research")

    def run(self) -> Dict[str, Any]:
        http_util = HttpUtil(base_url)
        response = http_util.getData(f"/dane/lab_data.zip", ResponseType.CONTENT)
        files = ZipUtil().extract_to_memory(response)

        # Initialize the variable to hold JSONL lines
        jsonl_lines = []

        for file_name, content in files.items():
            if not (file_name == "incorrect.txt" or file_name == "correct.txt"):
                continue

            valid = 1 if file_name == "correct.txt" else 0

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            lines = content.strip().split("\n")

            # Iterate over lines and create JSONL format
            for line in lines:

                # Create the JSONL entry
                jsonl_entry = {
                    "messages": [
                        {"role": "system", "content": "verify data correctness"},
                        {"role": "user", "content": line},
                        {"role": "assistant", "content": str(valid)}
                    ]
                }

                # Convert to JSON and append to the list
                jsonl_lines.append(json.dumps(jsonl_entry))

            script_dir = os.path.dirname(__file__)  # Directory of the script
            resource_dir = os.path.join(script_dir, 'resources')
            file_path = os.path.join(resource_dir, "fine_tune_data.jsonl")

            with open(file_path, "w") as f:
                f.write("\n".join(jsonl_lines))



