from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List

from app.adapters.base import BaseAdapter
from app.adapters.errors import AuthenticationError, FetchError
from app.adapters.slack.config import SlackConfig
from app.config import settings
from app.models.assets import NormalizedAsset

# Slack quirk worth knowing cold: the Web API returns HTTP 200 even on auth failure --
# errors show up as {"ok": false, "error": "invalid_auth"} in the body, not a 401/403 status.
# The shared client's httpx-status-based retry/auth-detection doesn't see this at all, so
# every call here has to check body["ok"] explicitly instead of relying on raise_for_status().
_AUTH_ERRORS = {"invalid_auth", "not_authed", "account_inactive", "token_revoked"}


class SlackAdapter(BaseAdapter):

    def __init__(self, config: SlackConfig):
        super().__init__(config)

    async def connect(self):
        resp = await self.client.request(
            method="GET", path="/conversations.list", params={"limit": 1}
        )
        body = resp.json()
        if not body.get("ok"):
            error = body.get("error", "unknown_error")
            if error in _AUTH_ERRORS:
                raise AuthenticationError(f"Slack authentication failed: {error}")
            raise FetchError(f"Slack connect check failed: {error}")

    async def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """Both axes can be large in a big workspace -- thousands of channels, and per-channel
        history -- so channels are yielded page by page too, not just per-channel messages,
        instead of requiring the full channel list up front. Per-channel history is one page per
        channel -- a deliberate v1 scope limit, not an oversight: unlike Auth0's roles, Slack has
        no batch/all-channels history endpoint, so per-channel calls are the API's actual shape,
        not an N+1 mistake to avoid. Full backfill would need a different, paginated-per-channel
        strategy tracked separately, not attempted here)."""
        async for channel_page in self.client.paginate_pages(
            path="/conversations.list",
            params={"types": ",".join(self.config.channel_types), "limit": 200},
            pagination="cursor_body",
            extract_data=lambda r: r["channels"],
        ):
            for channel in channel_page:
                history = await self.client.paginated_get(
                    path="/conversations.history",
                    params={"channel": channel["id"], "limit": self.config.message_history_limit},
                    pagination="cursor_body",
                    max_pages=1,
                    extract_data=lambda r: r["messages"],
                )
                if not history:
                    continue
                for msg in history:
                    msg["_channel_id"] = channel["id"]
                    msg["_channel_name"] = channel.get("name", channel["id"])
                yield history

    def normalize(self, raw_data: List[Dict]) -> list[NormalizedAsset]:
        """Required fields always populated: text can be genuinely empty for some message
        subtypes (file shares, block-only bot messages) -- name falls back to a placeholder
        rather than crashing the whole batch on one message subtype the schema didn't expect."""
        return [
            NormalizedAsset(
                asset_id=f"{msg['_channel_id']}_{msg['ts']}",
                customer_id=settings.customer_id,
                name=msg.get("text") or f"(no text - {msg.get('subtype', 'message')})",
                asset_type="message",
                status="ACTIVE",
                last_seen=datetime.fromtimestamp(float(msg["ts"]), tz=timezone.utc),
                vendor="Slack",
                metadata=msg,
            )
            for msg in raw_data
        ]
