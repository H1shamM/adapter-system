from datetime import datetime, timedelta
from typing import Optional
from pymongo import ASCENDING

from app.config import settings
from app.db.mongo import get_mongo_client
from app.utils.mongo import serialize_mongo


class AdapterConfigStore:
    def __init__(self):
        self.client = get_mongo_client()
        self.db = self.client[settings.database.mongo_db_name]
        self.collection = self.db.adapters

    def create_indexes(self):
        """Create indexes for adapters instances"""

        self.collection.create_index([("adapter_id", ASCENDING)], unique=True)

        self.collection.create_index([("adapter_type", ASCENDING)])

        #index for scheduler queries
        self.collection.create_index([
            ("enabled", ASCENDING),
            ("next_sync", ASCENDING),
        ])


    def _sanitize(self, doc: dict | None) -> dict | None:
        return serialize_mongo(doc)

    def upsert(self, adapter_id: str, adapter_type: str, config: dict):
        """Upsert an adapter instance config."""

        config_with_meta = {
            "adapter_id": adapter_id,
            "adapter_type": adapter_type,
            **config,
            "updated_at": datetime.utcnow()

        }

        self.collection.update_one(
            {"adapter_id": adapter_id},
            {"$set": config_with_meta},
            upsert=True,
        )

    def get(self, adapter_id: str):
        doc = self.collection.find_one({"adapter_id": adapter_id})
        return self._sanitize(doc)

    def get_by_type(self, adapter_type: str):
        cursor = self.collection.find({"adapter_type": adapter_type})
        return [self._sanitize(doc) for doc in cursor]

    def list_all(self):
        cursor = self.collection.find()
        return [self._sanitize(doc) for doc in cursor]

    def delete(self, adapter_id: str):
        """Delete an adapter instance by ID."""
        self.collection.delete_one({"adapter_id": adapter_id})

    def set_next_sync(self, adapter_id: str, sync_interval: int):

        next_sync = datetime.utcnow() + timedelta(seconds=sync_interval)

        self.collection.update_one(
            {"adapter_id": adapter_id},
            {
                "$set": {
                    "next_sync": next_sync,
                },
                "$setOnInsert": {
                    "last_sync": None
                }
            },
            upsert=True,
        )

    def get_due_adapters(self) -> list:

        now = datetime.utcnow()

        cursor = self.collection.find({
            "enabled": True,
            "$or": [
                {"next_sync": {"$lte": now}},
                {"next_sync": None}
            ]
        })

        return [serialize_mongo(doc) for doc in cursor]

    def update_after_sync(self, adapter_id: str):

        adapter = self.collection.find_one({"adapter_id": adapter_id})
        if not adapter:
            return

        sync_interval = adapter.get("sync_interval", 3600)
        now = datetime.utcnow()
        next_sync = now + timedelta(seconds=sync_interval)

        self.collection.update_one(
            {"adapter_id": adapter_id},
            {
                "$set": {
                    "last_sync": now,
                    "next_sync": next_sync,
                }
            }
        )