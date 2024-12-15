from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
import traceback
from neo4j import GraphDatabase

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')

neo4j_uri = os.getenv('NEO4J_URI')
neo4j_user = os.getenv('NEO4J_USER')
neo4j_password = os.getenv('NEO4J_PASSWORD')

class S03E05(BaseTask):
    def __init__(self):
        super().__init__(base_url,"connections")

    def run(self) -> Dict[str, Any]:

        try:

            persons_result = self.get_sql_result("select id, username from users")
            persons = persons_result['reply']
            self.logger.info(f"persons:  {persons}")

            connections_result = self.get_sql_result("select user1_id, user2_id from connections")
            connections = connections_result['reply']
            self.logger.info(f"connections:  {connections}")


            AUTH = (neo4j_user, neo4j_password)
            with GraphDatabase.driver(neo4j_uri, auth=AUTH, connection_timeout=20) as driver:
                driver.verify_connectivity()
                print("Connection established.")

                result,_,_ = driver.execute_query("RETURN 1 AS test")
                self.logger.info(f"result:  {result}")

                for person in persons:
                    self.logger.info(f"person:  {person}")
                    result,_,_ = driver.execute_query(
                        "CREATE (p:Person {name: $person.username, id: $person.id}) RETURN p",
                        person=person,
                        database_="neo4j",
                    )
                    self.logger.info(f"result:  {result}")

                for connection in connections:
                    self.logger.info(f"connection:  {connection}")
                    result,_,_ = driver.execute_query(
                    "MATCH (p1:Person {id: $connection.user1_id}), (p2:Person {id: $connection.user2_id}) CREATE (p1)-[:KNOW]->(p2);",
                    connection=connection,
                    database_="neo4j",
                    )
                    self.logger.info(f"result:  {result}")

                result,_,_ = driver.execute_query(
                    "MATCH (start:Person {name: 'Rafał'}), (end:Person {name: 'Barbara'}), p = shortestPath((start)-[:KNOW*]-(end)) return p;",
                    database_="neo4j",
                )

                person_names = []

                for record in result:  # Each record is a path in the result
                    path = record['p']  # 'p' is the alias for the shortest path in the query
                    for node in path.nodes:  # Extract nodes from the path
                        if 'name' in node:  # Check if the node has a 'name' property
                            person_names.append(node['name'])

                self.logger.info(f"person_names:  {person_names}")

                comma_separated_names = ", ".join(person_names)


            self.verify(comma_separated_names, "/report")


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

        return sql_result
