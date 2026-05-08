import random
from datetime import datetime, timedelta
from typing import Dict, List

from app.adapters.base import AdapterConfig, BaseAdapter
from app.config import settings
from app.models.assets import NormalizedAsset


class MockConfig(AdapterConfig):
    asset_types: list = ["endpoint", "user"]
    num_assets: int = 100


class MockAdapter(BaseAdapter):
    async def connect(self) -> None:
        return None

    async def fetch_raw(self) -> List[Dict]:
        return [self._generate_mock_asset() for _ in range(self.config.num_assets)]

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        return [
            NormalizedAsset(
                asset_id=f"mock_{asset['type']}_{asset['id']}",
                customer_id=settings.customer_id,
                name=asset["name"],
                asset_type=asset["type"],
                status=random.choice(["ACTIVE", "INACTIVE"]),
                last_seen=datetime.now() - timedelta(days=random.randint(0, 365)),
                vendor="Mock",
                metadata={"os": asset.get("os"), "last_user": asset.get("user")},
            )
            for asset in raw_data
        ]

    def _generate_mock_asset(self) -> Dict:
        asset_type = random.choice(self.config.asset_types)
        base = {
            "id": random.randint(1000, 9999),
            "name": f"{asset_type.capitalize()} {random.randint(1, 1000)}",
            "type": asset_type,
            "timestamp": datetime.now().isoformat(),
        }

        if asset_type == "endpoint":
            base.update(
                {
                    "os": random.choice(["Windows 10", "macOS 13", "Ubuntu 22.04"]),
                    "ip": ".".join(str(random.randint(0, 255)) for _ in range(4)),
                }
            )
        elif asset_type == "user":
            base.update(
                {
                    "email": f"user{random.randint(1, 1000)}@example.com",
                    "department": random.choice(["IT", "HR", "Finance"]),
                }
            )

        return base
