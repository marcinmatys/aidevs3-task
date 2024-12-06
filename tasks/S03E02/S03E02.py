from llmService.openaiService import OpenAIService
from embeddingService.openaiEmbeddingService import OpenAIEmbeddingService
from qdrantService.qdrantService import QdrantService
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
import io
import json
from typing import Dict, List, Any
from common.zipUtil import ZipUtil
from common.HttpUtil import HttpUtil, ResponseType
import traceback
import functools
from common.cache import persistent_cache
import uuid

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

class S03E02(BaseTask):

    def __init__(self):
        super().__init__(base_url,"wektory")
        self.persons = None
        self.qdrantService = QdrantService("mat-aidevs")

    def run(self) -> Dict[str, Any]:

        try:
            reports = self.get_reports()

            embeddings = self.get_embeddings_to_index(reports)

            self.index_points(embeddings, reports)

            query_embedding = self.get_embedding_for_query('W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?')

            response = self.qdrantService.search(query_embedding[0],10)
            response_payload = response[0].payload
            self.logger.info(f"response payload: {response_payload}")

            self.verify(response_payload['date'], "/report")

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()


    @persistent_cache(__file__)
    def get_embeddings_to_index(self, reports):
        embeddings = OpenAIEmbeddingService().get_embeddings([report.get('content') for report in reports])
        return embeddings

    def get_embedding_for_query(self, query):
        embeddings = OpenAIEmbeddingService().get_embeddings([query])
        return embeddings

    def index_points(self, embeddings, reports):

        points = []
        index = 0
        index_report = 0;
        for embedding in embeddings:
            point = {'id': str(uuid.uuid4()), 'vector': embedding, 'payload': {'date': reports[index_report].get('date'), 'text':reports[index_report].get('content')}}
            points.append(point)

            if index >= 10:
                self.qdrantService.upsert_points(points)
                points = []
                index = 0

            index += 1
            index_report += 1

        self.qdrantService.upsert_points(points)



    @persistent_cache(__file__)
    def get_reports(self) -> List[Dict[str,str]]:
        files = self.get_weapons_files()
        reports = []
        for name, content in files.items():
            content = content.decode('utf-8')

            paragraphs = self.split_content(content)

            file_name = os.path.basename(name)
            report_date = file_name.split('.')[0].replace('_', '-')

            for paragraph in paragraphs:
                reports.append({"date": report_date, "content": paragraph})

        return reports

    def get_weapons_files(self) -> Dict[str, bytes]:
        http_util = HttpUtil(base_url)
        response = http_util.getData(f"/dane/pliki_z_fabryki.zip", ResponseType.CONTENT)
        files = ZipUtil().extract_to_memory(response)
        for file_name, content in files.items():
            if file_name == "weapons_tests.zip":
                return ZipUtil().extract_to_memory(content,"1670")

    def split_content(self, content):
        # Extract the title from the first line
        lines = content.split("\n", 1)  # Split only at the first newline
        title = lines[0]
        remaining_text = lines[1].strip()  # Get the text after the first line and trim spaces

        # Split the remaining text into paragraphs using single newlines or double newlines
        paragraphs = [para.strip() for para in remaining_text.split("\n\n")]

        # Add the title to each paragraph
        titled_paragraphs = [f"{title}\n{para}" for para in paragraphs]

        # Print or process the result
        for part in titled_paragraphs:
            print(part)
            print("\n" + "-" * 40 + "\n")

        return titled_paragraphs

