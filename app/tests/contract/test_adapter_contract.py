"""Contract tests every adapter in ADAPTER_REGISTRY must satisfy.

These tests run against every registered adapter and verify it conforms
to the BaseAdapter interface beyond what the ABC enforces. The ABC only
checks that the methods *exist*; this suite checks they're async where
the base class awaits them, that normalize() returns NormalizedAsset
instances, and that an end-to-end execute() round-trip works.

Adding a new adapter requires adding entries to MINIMAL_CONFIGS and
SAMPLE_RAW_DATA below. That's intentional friction: contract data is
the contract.
"""

import copy
import inspect
from typing import Dict, List

import pytest

from app.adapters.factory import ADAPTER_REGISTRY
from app.models.assets import NormalizedAsset

# Minimal config kwargs that satisfy each adapter's ConfigClass.
# Keys must match ADAPTER_REGISTRY exactly.
MINIMAL_CONFIGS: Dict[str, dict] = {
    "github": {
        "name": "github-test",
        "base_url": "https://api.github.com",
        "auth_type": "bearer",
        "auth_config": {"token": "test-token"},
        "repo": "octocat/hello-world",
    },
    "aws": {
        "name": "aws-test",
        "base_url": "https://aws.amazon.com",
        "auth_type": "aws_sigv4",
        "auth_config": {
            "access_key": "AKIA-TEST",
            "secret_key": "test-secret",
            "region": "us-east-1",
        },
    },
    "mock": {
        "name": "mock-test",
        "base_url": "http://example.invalid",
        "num_assets": 3,
    },
    "jsonplaceholder": {
        "name": "jsonplaceholder-test",
        "base_url": "https://jsonplaceholder.typicode.com",
    },
    "coingecko": {
        "name": "coingecko-test",
        "base_url": "https://api.coingecko.com",
    },
    "randomuser": {
        "name": "randomuser-test",
        "base_url": "https://randomuser.me/api",
    },
    "perftest": {
        "name": "perftest-test",
        "base_url": "http://example.invalid",
        "test_id": "contract-test-1",
        "asset_count": 3,
        "sync_duration_seconds": 60,
    },
    "auth0": {
        "name": "auth0-test",
        "base_url": "https://dev-test.us.auth0.com",
        "domain": "dev-test.us.auth0.com",
        "auth_type": "oauth2_client_credentials",
        "auth_config": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "audience": "https://dev-test.us.auth0.com/api/v2/",
            "token_url": "https://dev-test.us.auth0.com/oauth/token",
        },
    },
    "slack": {
        "name": "slack-test",
        "base_url": "https://slack.com/api",
        "auth_type": "bearer",
        "auth_config": {"token": "xoxb-test-token"},
    },
}

# Representative raw response shapes. Each adapter's normalize() must
# accept this shape and produce NormalizedAsset instances.
SAMPLE_RAW_DATA: Dict[str, List[dict]] = {
    "github": [
        {
            "id": 1,
            "title": "Found a bug",
            "state": "open",
            "updated_at": "2024-01-01T00:00:00",
            "html_url": "https://github.com/octocat/hello-world/issues/1",
            "labels": [{"name": "bug"}],
        }
    ],
    "aws": [
        {
            "InstanceId": "i-0123456789abcdef0",
            "InstanceType": "t3.micro",
            "State": {"Name": "running"},
            "VpcId": "vpc-12345",
            "PublicIpAddress": "203.0.113.1",
            "LaunchTime": __import__("datetime").datetime(2024, 1, 1),
            "Tags": [{"Key": "Name", "Value": "web-1"}],
        }
    ],
    "mock": [
        {
            "id": 1234,
            "name": "Endpoint 1",
            "type": "endpoint",
            "timestamp": "2024-01-01T00:00:00",
            "os": "Ubuntu 22.04",
        }
    ],
    "jsonplaceholder": [{"id": 1, "name": "Alice", "email": "alice@example.com"}],
    "coingecko": [{"id": "bitcoin", "name": "Bitcoin"}],
    "randomuser": [
        {
            "login": {"uuid": "abc-123"},
            "name": {"first": "Alice", "last": "Smith"},
            "email": "alice@example.com",
        }
    ],
    "perftest": [
        {
            "id": "contract-test-1_asset_0",
            "name": "Test asset 0",
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
        }
    ],
    "auth0": [
        {
            "user_id": "auth0|contract-test-1",
            "name": "Contract Test User",
            "email": "contract-test@example.com",
            "email_verified": True,
            "updated_at": "2024-01-01T00:00:00.000Z",
            "created_at": "2024-01-01T00:00:00.000Z",
            "app_metadata": {"department": "Engineering"},
            "_roles": ["Viewer"],
        }
    ],
    "slack": [
        {
            "type": "message",
            "ts": "1704067200.000100",
            "text": "Contract test message",
            "user": "U0CONTRACT1",
            "_channel_id": "C0CONTRACT1",
            "_channel_name": "general",
        }
    ],
}

ALL_ADAPTERS = sorted(ADAPTER_REGISTRY.keys())


def _build(adapter_type: str):
    """Construct an adapter from its registered (Class, ConfigClass) pair."""
    adapter_cls, config_cls = ADAPTER_REGISTRY[adapter_type]
    config = config_cls(**MINIMAL_CONFIGS[adapter_type])
    return adapter_cls(config)


# ---------------------------------------------------------------------------
# Registry coverage: ensure the test data dicts stay in sync with the registry
# ---------------------------------------------------------------------------


def test_minimal_configs_cover_every_registered_adapter():
    missing = set(ADAPTER_REGISTRY) - set(MINIMAL_CONFIGS)
    extra = set(MINIMAL_CONFIGS) - set(ADAPTER_REGISTRY)
    assert not missing, f"MINIMAL_CONFIGS missing entries for: {missing}"
    assert not extra, f"MINIMAL_CONFIGS has stale entries: {extra}"


def test_sample_raw_data_covers_every_registered_adapter():
    missing = set(ADAPTER_REGISTRY) - set(SAMPLE_RAW_DATA)
    extra = set(SAMPLE_RAW_DATA) - set(ADAPTER_REGISTRY)
    assert not missing, f"SAMPLE_RAW_DATA missing entries for: {missing}"
    assert not extra, f"SAMPLE_RAW_DATA has stale entries: {extra}"


# ---------------------------------------------------------------------------
# Static contract: method signatures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_connect_is_async(adapter_type):
    cls = ADAPTER_REGISTRY[adapter_type][0]
    assert inspect.iscoroutinefunction(
        cls.connect
    ), f"{cls.__name__}.connect() must be async (BaseAdapter.execute() awaits it)"


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_fetch_raw_is_async(adapter_type):
    cls = ADAPTER_REGISTRY[adapter_type][0]
    assert inspect.iscoroutinefunction(
        cls.fetch_raw
    ), f"{cls.__name__}.fetch_raw() must be async (BaseAdapter.execute() awaits it)"


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_normalize_is_sync(adapter_type):
    cls = ADAPTER_REGISTRY[adapter_type][0]
    assert not inspect.iscoroutinefunction(
        cls.normalize
    ), f"{cls.__name__}.normalize() must be sync (BaseAdapter.execute() does not await it)"


# ---------------------------------------------------------------------------
# Construction contract: every registry entry instantiates from minimal config
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_construction_from_minimal_config(adapter_type):
    adapter = _build(adapter_type)
    assert adapter.config.name == MINIMAL_CONFIGS[adapter_type]["name"]


# ---------------------------------------------------------------------------
# Behavior contract: normalize()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_normalize_empty_input_returns_empty_list(adapter_type):
    adapter = _build(adapter_type)
    result = adapter.normalize([])
    assert result == [], f"{adapter_type}: normalize([]) must return []"


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_normalize_returns_normalized_assets(adapter_type):
    adapter = _build(adapter_type)
    sample = SAMPLE_RAW_DATA[adapter_type]
    result = adapter.normalize(sample)
    assert isinstance(result, list), f"{adapter_type}: normalize must return a list"
    assert len(result) == len(
        sample
    ), f"{adapter_type}: normalize must return one asset per input item"
    assert all(
        isinstance(item, NormalizedAsset) for item in result
    ), f"{adapter_type}: every element must be a NormalizedAsset"


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
def test_normalize_does_not_mutate_input(adapter_type):
    adapter = _build(adapter_type)
    sample = SAMPLE_RAW_DATA[adapter_type]
    original = copy.deepcopy(sample)
    adapter.normalize(sample)
    assert sample == original, f"{adapter_type}: normalize() must not mutate its input"


# ---------------------------------------------------------------------------
# End-to-end contract: execute() with mocked connect/fetch_raw
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_type", ALL_ADAPTERS)
async def test_execute_round_trip(adapter_type, mocker):
    adapter = _build(adapter_type)

    async def fake_connect():
        return None

    async def fake_fetch():
        return SAMPLE_RAW_DATA[adapter_type]

    mocker.patch.object(adapter, "connect", side_effect=fake_connect)
    mocker.patch.object(adapter, "fetch_raw", side_effect=fake_fetch)

    assets = await adapter.execute()

    assert isinstance(assets, list), f"{adapter_type}: execute() must return a list"
    assert len(assets) == len(
        SAMPLE_RAW_DATA[adapter_type]
    ), f"{adapter_type}: execute() must produce one asset per fetch_raw item"
    assert all(
        isinstance(a, NormalizedAsset) for a in assets
    ), f"{adapter_type}: every execute() result must be a NormalizedAsset"
