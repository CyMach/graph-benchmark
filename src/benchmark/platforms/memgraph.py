import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(".env")


class MemgraphAdapter:
    def __init__(self):
        self.uri = os.environ["MEMGRAPH_URI"]
        self.username = os.environ["MEMGRAPH_USERNAME"]
        self.password = os.environ["MEMGRAPH_PASSWORD"]

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    def connect(self):
        self.driver.verify_connectivity()
        print("Memgraph connection successful.")

    def execute(self, query, **parameters):
        # Do not pass database_= for Memgraph.
        return self.driver.execute_query(
            query,
            **parameters,
        )

    def close(self):
        self.driver.close()
