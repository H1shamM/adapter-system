from datetime import datetime
from typing import Dict, List

from app.adapters.base import BaseAdapter
from app.adapters.errors import FetchError, AuthenticationError
from app.models.assets import NormalizedAsset

class RandomUserAdapter(BaseAdapter):

    adapter_type = 'RandomUserAdapter'

    def connect(self):
        try:
            self.client.get("", params={'results': 1})
        except Exception as e:
            raise AuthenticationError("RandomUser connect failed") from e

    def fetch_raw(self) -> List[Dict]:

        try:
            users = self.client.paginated_get(
                path="",
                params={
                    "results": 50,
                    "seed":"adapter-system"
                },
                pagination="page_number",
                page_size=50,
                max_pages=5,
                extract_data= lambda data: data["results"]
            )
            return users
        except Exception as e:
            raise FetchError("RandomUser fetch failed") from e


    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:

        assets = []
        for data in raw_data:
            asset = NormalizedAsset.from_raw({
                "asset_id": data['login']["uuid"],
                "name": f"{data['name']['first']} - {data['name']['last']}",
                "asset_type": "user",
                "status": "active",
                "last_seen": datetime.utcnow(),
                "vendor": "randomuser",
                "metadata": data
            })
            assets.append(asset)

        return assets


