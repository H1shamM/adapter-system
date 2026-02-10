from datetime import datetime
from typing import List,Dict
from app.adapters.base import BaseAdapter, AdapterConfig
from app.models.assets import NormalizedAsset
from app.adapters.errors import FetchError


class CoinGeckoAdapter(BaseAdapter):

    adapter_name = 'coingecko'

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.currency = getattr(self.config,"currency","usd")

    def connect(self):
        self.client.get('/ping')

    def fetch_raw(self) -> List[Dict]:
        try:
            data = self.client.get(
                f"/api/v3/coins/markets?vs_currency={self.currency}&order=market_cap_desc"
            ).json()

            return data
        except Exception as e:
            raise FetchError("CoinGecko fetch failed") from e



    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        assets = []

        for data in raw_data:
            asset = NormalizedAsset.from_raw({
                "asset_id": data["id"],
                "name": data["name"],
                "asset_type": "crypto",
                "status": "active",
                "last_seen": datetime.utcnow(),
                "vendor": "coingecko",
                "metadata": data
            })
            assets.append(asset)

        return assets

