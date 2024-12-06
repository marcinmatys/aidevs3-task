from qdrant_client import QdrantClient, models
import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, List, Any

_ = load_dotenv(find_dotenv())
url = os.getenv('QDRANT_URL')
key = os.getenv('QDRANT_API_KEY')

client = QdrantClient(url=url)


class QdrantService:

    def __init__(self, collection_name:str = None):
        self.collection_name=collection_name
        self.remove_collection()
        self.add_collection()

    def upsert_points(self, points:List[Dict[str,Any]]):

        client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point['id'],
                    payload=point['payload'],
                    vector=point['vector'],
                )
                for point in points
            ],
        )

    def add_collection(self):

        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )

    def remove_collection(self):

        client.delete_collection(collection_name=self.collection_name)

    def search(self, query_vector:List[float], limit:int):

        response = client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
        )

        return response


