import os

from arango import ArangoClient
from dotenv import load_dotenv

load_dotenv(".env")


class ArangoDBAdapter:
    def __init__(self):
        self.url = os.environ["ARANGO_URL"]
        self.username = os.environ["ARANGO_USERNAME"]
        self.password = os.environ["ARANGO_PASSWORD"]
        self.database_name = os.getenv(
            "ARANGO_DATABASE",
            "mushroom_benchmark",
        )

        self.client = None
        self.db = None

    def connect(self):
        self.client = ArangoClient(
            hosts=self.url
        )

        system_db = self.client.db(
            "_system",
            username=self.username,
            password=self.password,
        )

        if not system_db.has_database(
            self.database_name
        ):
            system_db.create_database(
                self.database_name
            )

        self.db = self.client.db(
            self.database_name,
            username=self.username,
            password=self.password,
        )

        self.db.version()

        print(
            "ArangoGraph connection successful."
        )

    def execute(self, query, **parameters):
        if self.db is None:
            raise RuntimeError(
                "ArangoGraph is not connected."
            )

        return list(
            self.db.aql.execute(
                query,
                bind_vars=parameters,
            )
        )

    def close(self):
        self.db = None
        self.client = None
