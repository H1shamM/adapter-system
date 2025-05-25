from typing import List

from pymongo import MongoClient, DESCENDING, ASCENDING
from app.models.assets import NormalizedAsset

class AssetStore:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["asset_management"]
        self._create_indexes()

    def _create_indexes(self):
        self.db.assets.create_index("asset_id", unique=True)
        self.db.assets.create_index([("_last_modified", DESCENDING)])
        self.db.assets.create_index([("type", ASCENDING), ("status", ASCENDING)])


    def store_assets(self,assets: List[NormalizedAsset]):
        operations = []

        for asset in assets:
            operations.append({
                "updateOne" : {
                    'filter': {'asset_id': asset.asset_id},
                    'update' :{
                        '$set': asset.dict(),
                        '$inc' : {'version': 1},
                        '$currentDate': {'_last_modified': True}
                    },
                    'upsert': True

                }
            })
        return self.db.assets.bulk_write(operations)

    def find_assets(self, query: dict, skip: int = 0, limit: int = 50):
        return list(
            self.db.assets.find(query)
            .sort("_last_modified", DESCENDING)
            .skip(skip)
            .limit(limit)
            .max_time_ms(500)  # Prevent slow queries
        )

    def get_asset(self, asset_id: str) -> dict:
        return self.db.assets.find_one(
            {"asset_id": asset_id},
            max_time_ms=200  # Fail fast if slow
        )

    def get_asset_history(self, asset_id: str):
        return list(self.db.assets.find(
            {"asset_id": asset_id},
            sort=[("_last_modified", DESCENDING)],
            projection={"_id": 0, "version": 1, "_last_modified": 1}
        ))
