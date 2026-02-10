import logging
from typing import List

from pymongo import DESCENDING, ASCENDING, UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError

from app.db.mongo import get_mongo_client
from app.models.assets import NormalizedAsset

logger = logging.getLogger(__name__)


class AssetStore:
    def __init__(self):
        self.client = get_mongo_client()
        self.db = self.client["asset_management"]
        self.collection = self.db.assets
        self._create_indexes()

    def _create_indexes(self):
        self.db.assets.create_index([("asset_id",ASCENDING)], unique=True)
        self.db.assets.create_index([("_last_modified", DESCENDING)])
        self.db.assets.create_index([("type", ASCENDING), ("status", ASCENDING)])

    def store_assets(self, assets: List[NormalizedAsset]):
        operations = []

        for asset in assets:
            operations.append(
                UpdateOne(
                    filter={'asset_id': asset.asset_id},
                    update={
                        '$set': asset.dict(),
                        '$inc': {'version': 1},
                        '$currentDate': {'_last_modified': True}
                    },
                    upsert=True
                )
            )

        try:
            result = self.db.assets.bulk_write(operations)
            logger.info("Assets stored successfully", extra={"count": len(operations)})

            return result.bulk_api_result
        except BulkWriteError as e:
            logger.error("Bulk write error", exc_info=True)
            raise
        except PyMongoError as e:
            logger.error("MongoDB error", exc_info=True)
            raise

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
            maxTimeMS=200  # Fail fast if slow
        )

    def get_asset_history(self, asset_id: str):
        return list(self.db.assets.find(
            {"asset_id": asset_id},
            sort=[("_last_modified", DESCENDING)],
            projection={"_id": 0, "version": 1, "_last_modified": 1}
        ))

    def _normalize_asset(self, doc: dict):
        return {
            "id": doc["asset_id"],
            "type": doc["asset_type"],
            "status": doc["status"],
            "data": {
                "name": doc["name"],
                "vendor": doc["vendor"],
                "last_seen": doc["last_seen"],
                "metadata": doc.get("metadata", {}),
            }
        }

    def count_assets(self, query: dict) -> int:
        return self.db.assets.count_documents(query, maxTimeMS=500)

