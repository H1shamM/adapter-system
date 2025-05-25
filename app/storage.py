from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client["asset_management"]


def store_assets(assets: list) -> list:
    """Store normalized assets with deduplication"""
    if not assets:
        return []

    # Update existing or insert new
    operations = [
        {
            "updateOne": {
                "filter": {"asset_id": asset["asset_id"]},
                "update": {"$set": asset},
                "upsert": True
            }
        } for asset in assets
    ]

    result = db.assets.bulk_write(operations)
    return [str(id) for id in result.upserted_ids]
