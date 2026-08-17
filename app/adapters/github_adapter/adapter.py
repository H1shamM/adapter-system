from datetime import datetime
from typing import AsyncIterator, Dict, List

import httpx
from pydantic import Field

from app.adapters.base import AdapterConfig, BaseAdapter
from app.adapters.errors import AuthenticationError
from app.config import settings
from app.models.assets import NormalizedAsset


class GitHubConfig(AdapterConfig):
    """GitHub-specific configuration"""

    repo: str = Field(..., min_length=1)

    asset_types: List[str] = Field(default_factory=lambda: ["issue", "pull_request"])


class GitHubAdapter(BaseAdapter):

    def __init__(self, config: GitHubConfig):
        super().__init__(config)

    async def connect(self):
        try:
            await self.client.get(f"/repos/{self.config.repo}/issues")
            return None
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 401:
                raise AuthenticationError("GitHub authentication failed") from err
            raise

    async def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """Yields one chunk per issues page instead of collecting all pages first -- lets repos
        with large issue trackers be stored incrementally instead of all at once."""
        async for page in self.client.paginate_pages(
            f"/repos/{self.config.repo}/issues", max_pages=5, extract_data=lambda r: r
        ):
            yield page

    def normalize(self, raw_data: List[Dict]) -> list[NormalizedAsset]:
        return [
            NormalizedAsset(
                asset_id=f"github_{item['id']}",
                customer_id=settings.customer_id,
                name=item["title"],
                asset_type="issue",
                status=item["state"].upper(),
                last_seen=datetime.fromisoformat(item["updated_at"]),
                vendor="GitHub",
                metadata={
                    "url": item["html_url"],
                    "labels": [label["name"] for label in item.get("labels", [])],
                },
            )
            for item in raw_data
        ]
