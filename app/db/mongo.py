from pymongo import MongoClient

from app.config.settings import settings

_MONGO_CLIENT: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _MONGO_CLIENT

    if _MONGO_CLIENT is None:
        _MONGO_CLIENT = MongoClient(
            settings.database.mongo_url,
            maxPoolSize=settings.database.mongo_max_pool_size,
        )

    return _MONGO_CLIENT


def close_mongo_client():
    global _MONGO_CLIENT
    if _MONGO_CLIENT is not None:
        _MONGO_CLIENT.close()
        _MONGO_CLIENT = None
