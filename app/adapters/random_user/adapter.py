from datetime import datetime
from typing import AsyncIterator, Dict, List

from app.adapters.base import BaseAdapter
from app.adapters.errors import AuthenticationError, FetchError
from app.config import settings
from app.models.assets import NormalizedAsset


class RandomUserAdapter(BaseAdapter):

    adapter_type = "RandomUserAdapter"

    async def connect(self):
        try:
            await self.client.get("", params={"results": 1})
        except Exception as e:
            raise AuthenticationError("RandomUser connect failed") from e

    async def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """Yields one chunk per results page instead of collecting all pages first."""
        try:
            async for page in self.client.paginate_pages(
                path="",
                params={"results": 50, "seed": "adapter-system"},
                pagination="page_number",
                page_size=50,
                max_pages=5,
                extract_data=lambda data: data["results"],
            ):
                yield page
        except Exception as e:
            raise FetchError("RandomUser fetch failed") from e

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:

        assets = []
        for data in raw_data:
            asset = NormalizedAsset.from_raw(
                {
                    "asset_id": data["login"]["uuid"],
                    "customer_id": settings.customer_id,
                    "name": f"{data['name']['first']} - {data['name']['last']}",
                    "asset_type": "user",
                    "status": "active",
                    "last_seen": datetime.utcnow(),
                    "vendor": "randomuser",
                    "metadata": data,
                }
            )
            assets.append(asset)

        return assets
