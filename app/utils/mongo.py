from bson import ObjectId
from datetime import datetime

def serialize_mongo(value):
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [serialize_mongo(v) for v in value]

    if isinstance(value, dict):
        return {k: serialize_mongo(v) for k, v in value.items()}

    return value