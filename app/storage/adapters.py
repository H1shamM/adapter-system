from app.db.mongo import get_mongo_client
from app.utils.mongo import serialize_mongo


class AdapterConfigStore:
    def __init__(self):
        self.client = get_mongo_client()
        self.db = self.client["asset_management"]
        self.collection = self.db.adapters


    def _sanitize(self, doc: dict | None) -> dict | None:
        return serialize_mongo(doc)

    def upsert(self, name: str, config: dict):
        self.collection.update_one(
            {"name": name},
            {"$set": config},
            upsert=True,
        )

    def get(self, name: str):
        doc = self.collection.find_one({"name": name})
        return self._sanitize(doc)
