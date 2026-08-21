import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(".env")


class Neo4jAuraAdapter:
    def __init__(self):
        self.uri = os.environ["NEO4J_AURA_URI"]
        self.username = os.environ["NEO4J_AURA_USERNAME"]
        self.password = os.environ["NEO4J_AURA_PASSWORD"]
        self.database = os.getenv(
            "NEO4J_AURA_DATABASE",
            "neo4j",
        )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    def connect(self):
        self.driver.verify_connectivity()
        print("Neo4j Aura connection successful.")

    def execute(self, query, **parameters):
        return self.driver.execute_query(
            query,
            database_=self.database,
            **parameters,
        )

    def close(self):
        self.driver.close()
