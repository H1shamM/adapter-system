from pymongo import MongoClient, DESCENDING


class Queries:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["asset_management"]



    def find_assets(self, query: dict):
        return list(
            self.db.assets.find(query)
            .sort("_last_modified", DESCENDING)
            .limit(1000)
        )