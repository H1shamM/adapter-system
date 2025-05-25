import datetime
from typing import List, Dict, Literal
from app.adapters.base import BaseAdapter, AdapterConfig
import requests

from app.models.assets import NormalizedAsset


class GitHubAdapter(BaseAdapter):
    class GitHubConfig(AdapterConfig):
        """GitHub-specific configuration"""
        auth_type: Literal["bearer"] = "bearer"
        asset_types: List[str] = ["issue", "pull_request"]
        repo: str  # Additional GitHub-specific field

    def __init__(self, config: GitHubConfig):
        super().__init__(config)

    def connect(self) -> bool:
        response = self.session.get("https://api.github.com/user")
        return response.status_code == 200

    def fetch_raw(self) -> List[Dict]:
        return self.client.paginated_get(f"/repos/{self.config.repo}/issues")


    def normalize(self, raw_data: List[Dict]) -> list[NormalizedAsset]:
        return [
            NormalizedAsset(
                asset_id=f"github_{item['id']}",
                name=item['title'],
                asset_type="issue",
                status=item['state'].upper(),
                last_seen=datetime.fromisoformat(item['updated_at']),
                vendor="GitHub",
                metadata={
                    "url": item['html_url'],
                    "labels": [l['name'] for l in item.get('labels', [])]
                }
            ) for item in raw_data
        ]