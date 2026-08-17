from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.adapters.crowdstrike.adapter import CrowdStrikeAdapter
from app.adapters.crowdstrike.config import CrowdStrikeConfig
from app.adapters.errors import AuthenticationError
from app.models.assets import NormalizedAsset


@pytest.fixture
def crowdstrike_config():
    return CrowdStrikeConfig(
        name="crowdstrike",
        base_url="https://api.us-1.crowdstrike.com",
        auth_type="oauth2_client_credentials",
        auth_config={
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "token_url": "/oauth2/token",
            "token_body_format": "form",
        },
    )


# --- connect() ---
async def test_crowdstrike_connect_success(mocker, crowdstrike_config):
    adapter = CrowdStrikeAdapter(crowdstrike_config)
    mocker.patch.object(adapter.client, "ensure_token", new=AsyncMock(return_value=None))
    mocker.patch.object(adapter.client, "request", new=AsyncMock(return_value=None))
    await adapter.connect()


async def test_crowdstrike_connect_auth_failure(mocker, crowdstrike_config):
    adapter = CrowdStrikeAdapter(crowdstrike_config)
    mocker.patch.object(adapter.client, "ensure_token", new=AsyncMock(return_value=None))
    fake_response = httpx.Response(
        401,
        request=httpx.Request("GET", "https://api.us-1.crowdstrike.com/devices/queries/devices/v1"),
    )
    mocker.patch.object(
        adapter.client,
        "request",
        new=AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401", request=fake_response.request, response=fake_response
            )
        ),
    )
    with pytest.raises(AuthenticationError):
        await adapter.connect()


# --- fetch_raw() ---
async def test_crowdstrike_fetch_raw_devices_and_users_with_roles(mocker, crowdstrike_config):
    """Devices and user-UUIDs each come back as their own page (real fetch_raw() yields one page
    per paginate_pages call, not one combined list) -- proves per-page chunking. Per-uuid detail
    + roles enrichment runs via gather_bounded, no per-user N+1 beyond the 2 calls each uuid
    actually needs."""
    adapter = CrowdStrikeAdapter(crowdstrike_config)

    async def fake_paginate_pages(*args, path, **kwargs):
        if path == "/devices/combined/devices/v1":
            yield [{"device_id": "d1", "hostname": "host-1", "last_seen": "2026-08-05T00:00:00Z"}]
        elif path == "/user-management/queries/users/v1":
            yield ["u1", "u2"]  # user UUIDs
        else:
            raise AssertionError(f"unexpected path {path}")

    mocker.patch.object(
        adapter.client, "paginate_pages", new=MagicMock(side_effect=fake_paginate_pages)
    )

    def fake_request(method, path, params=None, **kwargs):
        if path == "/user-management/entities/users/v1":
            uuid = params["ids"]
            return httpx.Response(
                200,
                json={"resources": [{"uuid": uuid, "first_name": "A", "last_name": uuid}]},
                request=httpx.Request(method, "https://x" + path),
            )
        if path == "/user-management/combined/user-roles/v2":
            return httpx.Response(
                200,
                json={"resources": [{"role_name": f"Role-{params['user_uuid']}"}]},
                request=httpx.Request(method, "https://x" + path),
            )
        raise AssertionError(f"unexpected path {path}")

    mocker.patch.object(adapter.client, "request", new=AsyncMock(side_effect=fake_request))

    pages = [page async for page in adapter.fetch_raw()]

    assert adapter.client.paginate_pages.call_count == 2  # devices page + user-UUIDs page
    assert (
        adapter.client.request.call_count == 4
    )  # 2 users x (detail + roles), no per-user N+1 beyond that

    assert len(pages) == 2
    devices_page, users_page = pages
    assert len(devices_page) == 1
    assert devices_page[0]["_entity_type"] == "device"
    assert len(users_page) == 2
    assert all(u["_entity_type"] == "user" for u in users_page)
    roles_by_uuid = {u["uuid"]: u["_roles"] for u in users_page}
    assert roles_by_uuid == {"u1": ["Role-u1"], "u2": ["Role-u2"]}


# --- normalize() ---
def test_crowdstrike_normalize_device(crowdstrike_config):
    adapter = CrowdStrikeAdapter(crowdstrike_config)
    raw = [
        {
            "_entity_type": "device",
            "device_id": "d1",
            "hostname": "host-1",
            "status": "normal",
            "last_seen": "2026-08-05T00:00:00Z",
        }
    ]
    assets = adapter.normalize(raw)
    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].asset_id == "device_d1"
    assert assets[0].asset_type == "device"
    assert assets[0].status == "NORMAL"
    assert assets[0].last_seen == datetime.fromisoformat("2026-08-05T00:00:00Z")


def test_crowdstrike_normalize_user(crowdstrike_config):
    adapter = CrowdStrikeAdapter(crowdstrike_config)
    raw = [
        {
            "_entity_type": "user",
            "uuid": "u1",
            "first_name": "Alice",
            "last_name": "Tester",
            "_roles": ["Admin"],
        }
    ]
    assets = adapter.normalize(raw)
    assert len(assets) == 1
    assert assets[0].asset_id == "user_u1"
    assert assets[0].asset_type == "user"
    assert assets[0].name == "Alice Tester"
    assert assets[0].status == "ACTIVE"


def test_crowdstrike_normalize_user_missing_name_falls_back_to_uid(crowdstrike_config):
    adapter = CrowdStrikeAdapter(crowdstrike_config)
    raw = [{"_entity_type": "user", "uuid": "u2", "uid": "bob@example.com", "_roles": []}]
    assets = adapter.normalize(raw)
    assert assets[0].name == "bob@example.com"
