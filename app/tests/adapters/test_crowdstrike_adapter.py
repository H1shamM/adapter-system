from datetime import datetime
from unittest.mock import AsyncMock

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
    adapter = CrowdStrikeAdapter(crowdstrike_config)

    mocker.patch.object(
        adapter.client,
        "paginated_get",
        new=AsyncMock(
            side_effect=[
                [{"device_id": "d1", "hostname": "host-1", "last_seen": "2026-08-05T00:00:00Z"}],
                ["u1", "u2"],  # user UUIDs
            ]
        ),
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

    raw = await adapter.fetch_raw()

    assert adapter.client.paginated_get.call_count == 2  # devices call + user-UUIDs call
    assert (
        adapter.client.request.call_count == 4
    )  # 2 users x (detail + roles), no per-user N+1 beyond that

    devices = [r for r in raw if r["_entity_type"] == "device"]
    users = [r for r in raw if r["_entity_type"] == "user"]
    assert len(devices) == 1
    assert len(users) == 2
    assert users[0]["_roles"] == ["Role-u1"]


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
