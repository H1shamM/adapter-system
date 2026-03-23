import asyncio
import random
from datetime import datetime
from typing import Dict,List

from pydantic import Field

from app.adapters.base import BaseAdapter, AdapterConfig
from app.config import settings
from app.models.assets import NormalizedAsset


class PerfTestConfig(AdapterConfig):
    """ Performance test adapter configuration """

    test_id: str = Field(..., description="Unique test identifier")

    sync_duration_seconds: int = Field(
        default= 1800,
        description="How long this sync should take (in seconds)"
    )

    asset_count: int = Field(
        default=100,
        description="How many assets to generate)"
    )

    failure_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Chance of failure (0.0 to 1.0)"
    )


class PerfTestAdapter(BaseAdapter):
    """ Adapter that simulates long-running operations for testing """

    def __init__(self, config: PerfTestConfig):
        super().__init__(config)
        self.config: PerfTestConfig = config

    async def connect(self):
        await asyncio.sleep(1)

        if random.random() < self.config.failure_rate:
            raise Exception(f"Simulated connection failure for {self.config.test_id}")

        return True

    async def fetch_raw(self) -> List[Dict]:
        print(f"[{self.config.test_id}] Starting sync - will take {self.config.sync_duration_seconds} seconds")

        chunk_duration = 10
        chunks = self.config.sync_duration_seconds // chunk_duration

        for i in range(chunks):
            await asyncio.sleep(chunk_duration)
            progress = (i + 1) / chunks * 100
            print(f"[{self.config.test_id}] Progress: {progress:.0f}%")

        return [
            {
                "id": f"{self.config.test_id}_asset_{i}",
                "name": f"Test asset {i}",
                "status": random.choice(["active", "inactive","pending"]),
                "created_at": datetime.now().isoformat(),
            }
            for i in range(self.config.asset_count)
        ]

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        return [
            NormalizedAsset(
                asset_id=f"perftest_{item['id']}",
                customer_id=settings.customer_id,
                name=item["name"],
                asset_type="test_asset",
                status= item["status"].upper(),
                last_seen=datetime.fromisoformat(item["created_at"]),
                vendor=f"PrefTest- {self.config.test_id}",
                metadata={
                    "test_id": self.config.test_id,
                    "sync_duration": self.config.sync_duration_seconds,
                }
            )
            for item in raw_data
        ]

