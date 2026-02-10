import os

from pymongo import MongoClient

_MONGO_CLIENT = None


def get_mongo_client() -> MongoClient:
    global _MONGO_CLIENT

    if _MONGO_CLIENT is None:
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")

        if not mongo_url:
            raise RuntimeError("MONGO_URL not set")

        _MONGO_CLIENT = MongoClient(mongo_url)

    return _MONGO_CLIENT
