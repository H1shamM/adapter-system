from pymongo import DESCENDING

from app.db.mongo import get_mongo_client


class Queries:
    def __init__(self):
        self.client = get_mongo_client()
        self.db = self.client["asset_management"]

    def find_assets(self, query: dict):
        return list(
            self.db.assets.find(query)
            .sort("_last_modified", DESCENDING)
            .limit(1000)
        )
