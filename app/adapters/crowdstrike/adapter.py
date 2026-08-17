from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List

import httpx

from app.adapters.base import BaseAdapter
from app.adapters.crowdstrike.config import CrowdStrikeConfig
from app.adapters.errors import AuthenticationError
from app.config import settings
from app.models.assets import NormalizedAsset

_PAGINATION_KWARGS = {
    "pagination": "cursor_body",
    "cursor_response_path": "meta.pagination.offset",
    "cursor_param_name": "offset",
}


class CrowdStrikeAdapter(BaseAdapter):

    def __init__(self, config: CrowdStrikeConfig):
        super().__init__(config)

    async def connect(self):
        """Unlike Slack, CrowdStrike follows normal REST conventions -- real 401/403 status
        codes on auth failure, so this uses the same httpx.HTTPStatusError pattern as Auth0/
        GitHub, not Slack's body-inspection workaround."""
        try:
            await self.client.ensure_token()
            await self.client.request(
                method="GET", path="/devices/queries/devices/v1", params={"limit": 1}
            )
        except httpx.HTTPStatusError as err:
            if err.response.status_code in (401, 403):
                raise AuthenticationError(f"CrowdStrike authentication failed: {err}") from err
            raise

    async def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """Devices come back fully hydrated from one combined endpoint -- trivially streamable
        per page, no query-then-hydrate step needed. Users are the opposite: queryUserV1 returns
        UUIDs only, and per-user role assignments (CombinedUserRolesV2) are confirmed to take a
        single user_uuid -- no batch-roles endpoint exists, so that N+1 is the API's actual shape,
        not a design mistake (same situation as Slack's per-channel history calls). That per-uuid
        enrichment runs with bounded concurrency (gather_bounded) instead of one uuid at a time,
        since a page of up to 500 uuids at 2 sequential round trips each would otherwise be the
        real bottleneck for a fleet with millions of users. User DETAIL fetching is also done
        per-UUID rather than batched: CrowdStrike's docs strongly imply a batch entities endpoint
        exists (matching the devices pattern), but the exact path wasn't confirmed against real
        docs content, so this uses the one confirmed-safe path per user instead of guessing at an
        unverified batch endpoint -- worth revisiting once verified against a live account."""
        device_params = {"limit": 500}
        if self.config.device_filter:
            device_params["filter"] = self.config.device_filter

        async for page in self.client.paginate_pages(
            path="/devices/combined/devices/v1",
            params=device_params,
            extract_data=lambda r: r["resources"],
            **_PAGINATION_KWARGS,
        ):
            for device in page:
                device["_entity_type"] = "device"
            yield page

        async for uuid_page in self.client.paginate_pages(
            path="/user-management/queries/users/v1",
            params={"limit": 500},
            extract_data=lambda r: r["resources"],
            **_PAGINATION_KWARGS,
        ):
            if not uuid_page:
                continue
            yield await self.client.gather_bounded(
                [self._fetch_user(uuid) for uuid in uuid_page],
                limit=self.config.max_concurrent_requests,
            )

    async def _fetch_user(self, uuid: str) -> Dict:
        """Per-user detail + roles -- 2 sequential calls, the API's actual shape (no batch-roles
        endpoint exists). Extracted so fetch_raw() can run these concurrently per page via
        gather_bounded instead of one uuid at a time."""
        detail_resp = await self.client.request(
            "GET", "/user-management/entities/users/v1", params={"ids": uuid}
        )
        detail_resources = detail_resp.json().get("resources", [])
        user = detail_resources[0] if detail_resources else {"uuid": uuid}

        roles_resp = await self.client.request(
            "GET", "/user-management/combined/user-roles/v2", params={"user_uuid": uuid}
        )
        roles = [
            r.get("role_name") or r.get("role_id") for r in roles_resp.json().get("resources", [])
        ]

        user["_entity_type"] = "user"
        user["_roles"] = roles
        return user

    def normalize(self, raw_data: List[Dict]) -> list[NormalizedAsset]:
        """Devices and users are mapped differently because their real fields differ -- devices
        have a genuine last_seen from the Falcon sensor; the User entity has no confirmed
        last-modified timestamp, so last_seen falls back to sync time for users specifically
        (noted explicitly, not silently) rather than inventing a field name that was never
        confirmed against real docs content."""
        assets = []
        for item in raw_data:
            if item.get("_entity_type") == "device":
                assets.append(
                    NormalizedAsset(
                        asset_id=f"device_{item['device_id']}",
                        customer_id=settings.customer_id,
                        name=item.get("hostname") or item["device_id"],
                        asset_type="device",
                        status=(item.get("status") or "unknown").upper(),
                        last_seen=datetime.fromisoformat(
                            item.get("last_seen") or item.get("first_seen")
                        ),
                        vendor="CrowdStrike",
                        metadata=item,
                    )
                )
            else:
                name = f"{item.get('first_name', '')} {item.get('last_name', '')}".strip()
                assets.append(
                    NormalizedAsset(
                        asset_id=f"user_{item.get('uuid', item.get('uid'))}",
                        customer_id=settings.customer_id,
                        name=name or item.get("uid") or item.get("uuid"),
                        asset_type="user",
                        status=(item.get("status") or "ACTIVE").upper(),
                        last_seen=datetime.now(timezone.utc),
                        vendor="CrowdStrike",
                        metadata=item,
                    )
                )
        return assets
