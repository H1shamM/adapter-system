"""Mock-ENDPOINT tests -- a different tier from test_crowdstrike_adapter.py.

Those tests mock adapter.client.request()/paginated_get() directly, which verifies the adapter's
business logic but bypasses AssetHttpClient's real code entirely (retry loop, URL construction,
the cursor_body pagination logic itself). These tests instead mock httpx at the TRANSPORT layer
(via respx), with response bodies shaped exactly like CrowdStrike's real documented fields -- so
the adapter's real request()/paginated_get()/ensure_token() code actually runs against them.

This is the standard verification-layer tier for when no live vendor account exists (see
docs/AGENTIC_ADAPTER_DESIGN.md) -- it would have caught bugs like the Auth0 URL-concatenation bug
even without a real tenant, because the real URL-building code is what's actually exercised here.
"""

import respx
from httpx import Response

from app.adapters.crowdstrike.adapter import CrowdStrikeAdapter
from app.adapters.crowdstrike.config import CrowdStrikeConfig

BASE = "https://api.us-1.crowdstrike.com"


def _config():
    return CrowdStrikeConfig(
        name="crowdstrike",
        base_url=BASE,
        auth_type="oauth2_client_credentials",
        auth_config={
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "token_url": "/oauth2/token",
            "token_body_format": "form",
        },
    )


@respx.mock
async def test_crowdstrike_real_http_layer_end_to_end():
    # Token endpoint -- real ensure_token() code runs, form-encoded per token_body_format.
    token_route = respx.post(f"{BASE}/oauth2/token").mock(
        return_value=Response(200, json={"access_token": "fake-token", "expires_in": 1800})
    )

    # connect()'s cheap check.
    respx.get(f"{BASE}/devices/queries/devices/v1", params={"limit": "1"}).mock(
        return_value=Response(200, json={"resources": [], "meta": {}})
    )

    # Devices: two pages via the real cursor_body pagination code, meta.pagination.offset.
    devices_route = respx.get(f"{BASE}/devices/combined/devices/v1")
    devices_route.side_effect = [
        Response(
            200,
            json={
                "resources": [
                    {
                        "device_id": "d1",
                        "hostname": "host-1",
                        "status": "normal",
                        "last_seen": "2026-08-05T00:00:00Z",
                    }
                ],
                "meta": {"pagination": {"offset": "page2token"}},
            },
        ),
        Response(
            200,
            json={
                "resources": [
                    {
                        "device_id": "d2",
                        "hostname": "host-2",
                        "status": "normal",
                        "last_seen": "2026-08-05T00:00:00Z",
                    }
                ],
                "meta": {"pagination": {}},  # no offset -> real code stops here
            },
        ),
    ]

    # Users: one page of UUIDs via the same real cursor_body code.
    respx.get(f"{BASE}/user-management/queries/users/v1").mock(
        return_value=Response(200, json={"resources": ["u1"], "meta": {"pagination": {}}})
    )

    # Per-user detail + roles -- real per-user N+1 request() calls.
    respx.get(f"{BASE}/user-management/entities/users/v1", params={"ids": "u1"}).mock(
        return_value=Response(
            200, json={"resources": [{"uuid": "u1", "first_name": "Alice", "last_name": "Tester"}]}
        )
    )
    respx.get(f"{BASE}/user-management/combined/user-roles/v2", params={"user_uuid": "u1"}).mock(
        return_value=Response(200, json={"resources": [{"role_name": "Admin"}]})
    )

    adapter = CrowdStrikeAdapter(_config())
    await adapter.connect()
    raw = await adapter.fetch_raw()
    assets = adapter.normalize(raw)

    # Real pagination code walked both device pages.
    assert devices_route.call_count == 2
    devices = [a for a in assets if a.asset_type == "device"]
    users = [a for a in assets if a.asset_type == "user"]
    assert {d.metadata["device_id"] for d in devices} == {"d1", "d2"}
    assert len(users) == 1
    assert users[0].metadata["_roles"] == ["Admin"]

    # Real ensure_token() actually form-encoded the request, not JSON.
    token_request = token_route.calls[0].request
    assert token_request.headers["content-type"].startswith("application/x-www-form-urlencoded")
    body = token_request.content.decode()
    assert "client_id=test-client-id" in body
    assert "grant_type" not in body  # CrowdStrike shape: no grant_type/audience, unlike Auth0

    await adapter.close()
