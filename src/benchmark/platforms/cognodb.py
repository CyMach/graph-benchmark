import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


class CognoDBAdapter:

    def __init__(self):
        self.uri = os.environ["COGNODB_URI"]
        self.username = os.environ["COGNODB_USERNAME"]
        self.password = os.environ["COGNODB_PASSWORD"]
        self.database = os.getenv("COGNODB_DATABASE", "neo4j")

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )

    def connect(self):
        self.driver.verify_connectivity()
        print("CognoDB connection successful.")

    def execute(self, query, **parameters):
        return self.driver.execute_query(
            query,
            database_=self.database,
            **parameters,
        )

    def close(self):
        self.driver.close()
