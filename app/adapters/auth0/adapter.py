from datetime import datetime
from typing import Dict, List

import httpx

from app.adapters.auth0.config import Auth0Config
from app.adapters.base import BaseAdapter
from app.adapters.errors import AuthenticationError
from app.config import settings
from app.models.assets import NormalizedAsset


class Auth0Adapter(BaseAdapter):

    def __init__(self, config: Auth0Config):
        super().__init__(config)

    async def connect(self):
        try:
            await self.client.ensure_token()
            await self.client.request(method="GET", path="/api/v2/users?per_page=1")
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 401:
                raise AuthenticationError("Auth0 authentication failed") from err
            raise

    async def fetch_raw(self) -> List[Dict]:
        """Batch-fetch roles once and invert into a {user_id: [role_names]} map, instead of
        calling /api/v2/users/{id}/roles per user -- avoids N+1 at the cost of two extra calls
        total (roles + each role's users), regardless of user count."""
        users = await self.client.paginated_get(
            path="/api/v2/users", pagination="page_number", extract_data=lambda r: r
        )
        roles = await self.client.paginated_get(
            path="/api/v2/roles", pagination="page_number", extract_data=lambda r: r
        )
        user_roles: dict[str, list[str]] = {}
        for role in roles:
            role_id = role["id"]
            role_users = await self.client.paginated_get(
                path=f"/api/v2/roles/{role_id}/users",
                pagination="page_number",
                extract_data=lambda r: r,
            )
            for user in role_users:
                user_roles.setdefault(user["user_id"], []).append(role["name"])

        for user in users:
            user["_roles"] = user_roles.get(user["user_id"], [])

        return users

    def normalize(self, raw_data: List[Dict]) -> list[NormalizedAsset]:
        """name/last_seen fall back to email/created_at since not every Auth0 user object
        populates them the same way (tenant-configurable custom attributes) -- a record missing
        BOTH name and email still fails loudly via NormalizedAsset's required-field validation,
        by design (see Story 2 in axonius_stories_bank.md: silently dropping is worse)."""
        return [
            NormalizedAsset(
                asset_id=user.get("user_id"),
                customer_id=settings.customer_id,
                name=user.get("name") or user.get("email"),
                asset_type="user",
                status="BLOCKED" if user.get("blocked") else "ACTIVE",
                last_seen=datetime.fromisoformat(user.get("updated_at") or user.get("created_at")),
                vendor="Auth0",
                metadata=user,
            )
            for user in raw_data
        ]
