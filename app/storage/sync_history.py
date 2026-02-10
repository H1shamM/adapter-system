from datetime import datetime

from pymongo import ASCENDING, DESCENDING

from app.db.mongo import get_mongo_client

from app.utils.mongo import serialize_mongo


class SyncHistoryStore:
    def __init__(self):
        self.client = get_mongo_client()
        self.db = self.client["asset_management"]
        self.collection = self.db.sync_history
        self._create_indexes()

    def _create_indexes(self):
        self.collection.create_index([("sync_id", ASCENDING)], unique=True)
        self.collection.create_index([("adapter", ASCENDING)])
        self.collection.create_index([("started_at", DESCENDING)])


    def _sanitize(self, doc: dict | None) -> dict | None:
        return serialize_mongo(doc)

    def start_sync(self, *, sync_id: str, adapter: str):
        now = datetime.utcnow()

        self.collection.insert_one({
            "sync_id": sync_id,
            "adapter": adapter,
            "status": "STARTED",
            "started_at": now,
            "finished_at": None,
            "duration_ms": None,
            "result": None,
            "error": None,
        })

    def finish_sync(self, *, sync_id: str, status: str, result: dict | None = None, error: str | None = None):
        end = datetime.utcnow()

        doc = self.collection.find_one({"sync_id": sync_id})
        duration_ms = None
        if doc and doc.get("started_at"):
            duration_ms = int((end - doc.get("started_at")).total_seconds() * 1000)

        self.collection.update_one(
            {"sync_id": sync_id},
            {"$set": {
                "status": status,
                "finished_at": end,
                "duration_ms": duration_ms,
                "result": result,
                "error": error,
            }})

    def list(self, *, adapter: str | None = None, limit: int = 100):
        query = {}
        if adapter:
            query["adapter"] = adapter

        docs = (((self.collection
                  .find(query))
                 .sort("started_at", -1))
                .limit(limit))

        return [self._sanitize(doc) for doc in docs]

    def get(self, sync_id: str):
        return self._sanitize(self.collection.find_one({"sync_id": sync_id}))
