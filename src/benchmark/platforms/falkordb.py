import os

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv(".env")


class FalkorDBAdapter:
    def __init__(self):
        self.host = os.environ["FALKORDB_HOST"]
        self.port = int(os.environ["FALKORDB_PORT"])
        self.username = os.getenv("FALKORDB_USERNAME")
        self.password = os.getenv("FALKORDB_PASSWORD")

        self.graph_name = os.getenv(
            "FALKORDB_GRAPH",
            "mushroom_benchmark",
        )

        self.ssl = os.getenv(
            "FALKORDB_SSL",
            "true",
        ).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        self.client = None
        self.graph = None

    def connect(self):
        kwargs = {
            "host": self.host,
            "port": self.port,
            "ssl": self.ssl,
        }

        if self.username:
            kwargs["username"] = self.username

        if self.password:
            kwargs["password"] = self.password

        self.client = FalkorDB(**kwargs)
        self.graph = self.client.select_graph(
            self.graph_name
        )

        # Basic query test.
        self.graph.query("RETURN 1")

        print("FalkorDB connection successful.")

    def execute(self, query, **parameters):
        if self.graph is None:
            raise RuntimeError(
                "FalkorDB is not connected."
            )

        return self.graph.query(
            query,
            params=parameters,
        )

    def close(self):
        self.graph = None
        self.client = None
