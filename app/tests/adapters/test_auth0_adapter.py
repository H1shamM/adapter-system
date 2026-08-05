from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from app.adapters.auth0.adapter import Auth0Adapter
from app.adapters.auth0.config import Auth0Config
from app.adapters.errors import AuthenticationError
from app.models.assets import NormalizedAsset


@pytest.fixture
def auth0_config():
    return Auth0Config(
        name="auth0",
        base_url="https://dev-test.us.auth0.com",
        domain="dev-test.us.auth0.com",
        auth_type="oauth2_client_credentials",
        auth_config={
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "audience": "https://dev-test.us.auth0.com/api/v2/",
            "token_url": "https://dev-test.us.auth0.com/oauth/token",
        },
    )


# --- connect() ---
async def test_auth0_connect_success(mocker, auth0_config):
    #   - mock adapter.client.ensure_token with AsyncMock() (succeeds, no exception)
    #   - mock adapter.client.request with AsyncMock() (succeeds)
    #   - await adapter.connect() and assert it doesn't raise
    adapter = Auth0Adapter(auth0_config)
    mocker.patch.object(adapter.client, "ensure_token", new=AsyncMock(return_value=None))
    mocker.patch.object(adapter.client, "request", new=AsyncMock(return_value=None))

    await adapter.connect()


async def test_auth0_connect_auth_failure(mocker, auth0_config):
    #   - mock adapter.client.ensure_token to raise httpx.HTTPStatusError with a 401 response
    #     (build a fake httpx.Response(401, request=...) to attach)
    #   - assert connect() raises AuthenticationError, not the raw httpx error
    adapter = Auth0Adapter(auth0_config)
    fake_response = httpx.Response(401, request=httpx.Request("POST", "https://x/oauth/token"))
    mocker.patch.object(
        adapter.client,
        "ensure_token",
        new=AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401", request=fake_response.request, response=fake_response
            )
        ),
    )
    with pytest.raises(AuthenticationError):
        await adapter.connect()


# --- fetch_raw() ---
async def test_auth0_fetch_raw_batches_roles_not_per_user(mocker, auth0_config):

    # - mock adapter.client.paginated_get with an AsyncMock whose side_effect returns, in order:
    #       1. the users list (2 users)
    #       2. the roles list (2 roles: Admin, Viewer)
    #       3. role_users for role 1
    #       4. role_users for role 2
    #   - assert paginated_get was called exactly 4 times total (proves NO per-user role call --
    #     this is the actual thing this adapter exists to prove, make the assertion explicit)
    #   - assert each returned user dict has the correct "_roles" list
    adapter = Auth0Adapter(auth0_config)
    mocker.patch.object(
        adapter.client,
        "paginated_get",
        new=AsyncMock(
            side_effect=[
                [{"user_id": "u1"}, {"user_id": "u2"}],  # 1st call: users
                [{"id": "r1", "name": "Admin"}, {"id": "r2", "name": "Viewer"}],  # 2nd call: roles
                [{"user_id": "u1"}],  # 3rd call: role r1's users
                [{"user_id": "u2"}],  # 4th call: role r2's users
            ]
        ),
    )
    users = await adapter.fetch_raw()
    assert adapter.client.paginated_get.call_count == 4
    for user in users:
        assert len(user["_roles"]) == 1


# --- normalize() ---
def test_auth0_normalize_rich_user(auth0_config):
    adapter = Auth0Adapter(auth0_config)
    raw = [
        {
            "user_id": "auth0|1",
            "name": "Alice Tester",
            "email": "alice@example.com",
            "updated_at": "2026-08-04T08:59:03.789Z",
            "created_at": "2026-08-04T08:59:03.789Z",
            "app_metadata": {"employee_id": "E001"},
            "_roles": ["Admin", "Viewer"],
        }
    ]
    assets = adapter.normalize(raw)
    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].asset_id == "auth0|1"
    assert assets[0].name == "Alice Tester"
    assert assets[0].status == "ACTIVE"


def test_auth0_normalize_sparse_user_uses_fallbacks(auth0_config):
    #   - build a raw dict with NO "name" key (only "email"), NO "updated_at" (only "created_at"),
    #     NO app_metadata/given_name/family_name -- basically Bob's real shape
    #   - assert it does NOT raise, and name/last_seen fell back to email/created_at
    adapter = Auth0Adapter(auth0_config)
    raw = [
        {
            "user_id": "auth0|2",
            "name": "",
            "email": "alice@example.com",
            "created_at": "2026-08-04T08:59:03.789Z",
            "roles": ["Viewer"],
        }
    ]
    assets = adapter.normalize(raw)
    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].asset_id == "auth0|2"
    assert assets[0].name == "alice@example.com"
    assert assets[0].last_seen == datetime.fromisoformat("2026-08-04T08:59:03.789Z")
    assert assets[0].status == "ACTIVE"


def test_auth0_normalize_blocked_user(auth0_config):
    #   - raw dict with "blocked": True
    #   - assert status == "BLOCKED"
    adapter = Auth0Adapter(auth0_config)
    raw = [
        {
            "user_id": "auth0|1",
            "name": "Alice Tester",
            "email": "alice@example.com",
            "updated_at": "2026-08-04T08:59:03.789Z",
            "created_at": "2026-08-04T08:59:03.789Z",
            "app_metadata": {"employee_id": "E001"},
            "blocked": True,
            "_roles": ["Admin", "Viewer"],
        }
    ]
    assets = adapter.normalize(raw)
    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].asset_id == "auth0|1"
    assert assets[0].status == "BLOCKED"


def test_auth0_normalize_missing_name_and_email_raises(auth0_config):
    #   - raw dict with NEITHER "name" NOR "email"
    #   - assert this actually raises (pydantic ValidationError) -- documents that the fallback
    #     chain has a real bottom, on purpose, per the Story 2 lesson in axonius_stories_bank.md
    adapter = Auth0Adapter(auth0_config)
    raw = [
        {
            "user_id": "auth0|1",
            "updated_at": "2026-08-04T08:59:03.789Z",
            "created_at": "2026-08-04T08:59:03.789Z",
            "app_metadata": {"employee_id": "E001"},
            "_roles": ["Admin", "Viewer"],
        }
    ]

    with pytest.raises(ValidationError):
        adapter.normalize(raw)
