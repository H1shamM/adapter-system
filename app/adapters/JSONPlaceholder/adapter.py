from datetime import datetime
from typing import Dict, List

from app.adapters.base import BaseAdapter
from app.adapters.errors import FetchError
from app.models.assets import NormalizedAsset


class JSONPlaceholderAdapter(BaseAdapter):
    adapter_type = "jsonplaceholder"

    def connect(self):
        self.client.get('/users', params={"_limit": 1})

    def fetch_raw(self) -> List[Dict]:
        try:
            users = self.client.get('/users').json()
            return users
        except Exception as e:
            raise FetchError("JSONPlaceholderAdapter fetch failed") from e

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        assets = []

        for data in raw_data:
            asset = NormalizedAsset.from_raw({
                "asset_id": str(data["id"]),
                "name": data["name"],
                "asset_type": "user",
                "status": "active",
                "last_seen": datetime.utcnow(),
                "vendor": "jsonplaceholder",
                "metadata": data
            })
            assets.append(asset)

        return assets
