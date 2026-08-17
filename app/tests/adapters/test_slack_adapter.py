from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.adapters.errors import AuthenticationError, FetchError
from app.adapters.slack.adapter import SlackAdapter
from app.adapters.slack.config import SlackConfig
from app.models.assets import NormalizedAsset


@pytest.fixture
def slack_config():
    return SlackConfig(
        name="slack",
        base_url="https://slack.com/api",
        auth_type="bearer",
        auth_config={"token": "xoxb-test-token"},
    )


def _fake_response(json_data):
    class FakeResponse:
        def json(self):
            return json_data

    return FakeResponse()


# --- connect() ---
async def test_slack_connect_success(mocker, slack_config):
    adapter = SlackAdapter(slack_config)
    mocker.patch.object(
        adapter.client, "request", new=AsyncMock(return_value=_fake_response({"ok": True}))
    )
    await adapter.connect()


async def test_slack_connect_auth_failure(mocker, slack_config):
    adapter = SlackAdapter(slack_config)
    mocker.patch.object(
        adapter.client,
        "request",
        new=AsyncMock(return_value=_fake_response({"ok": False, "error": "invalid_auth"})),
    )
    with pytest.raises(AuthenticationError):
        await adapter.connect()


async def test_slack_connect_non_auth_failure_raises_fetch_error(mocker, slack_config):
    adapter = SlackAdapter(slack_config)
    mocker.patch.object(
        adapter.client,
        "request",
        new=AsyncMock(return_value=_fake_response({"ok": False, "error": "rate_limited"})),
    )
    with pytest.raises(FetchError):
        await adapter.connect()


# --- fetch_raw() ---
async def test_slack_fetch_raw_yields_one_page_per_channel(mocker, slack_config):
    """Channels are yielded page by page (not required up front for a huge workspace), and each
    channel's history is yielded as its own page instead of collecting every channel's messages
    into one list first."""
    adapter = SlackAdapter(slack_config)

    async def fake_paginate_pages(*args, **kwargs):
        yield [{"id": "C1", "name": "general"}, {"id": "C2", "name": "random"}]

    mocker.patch.object(
        adapter.client, "paginate_pages", new=MagicMock(side_effect=fake_paginate_pages)
    )
    mocker.patch.object(
        adapter.client,
        "paginated_get",
        new=AsyncMock(
            side_effect=[
                [{"ts": "1.1", "text": "hi"}],  # C1 history
                [{"ts": "2.1", "text": "yo"}],  # C2 history
            ]
        ),
    )

    pages = [page async for page in adapter.fetch_raw()]

    assert len(pages) == 2  # one page per channel, not one page for the whole workspace
    assert pages[0][0]["_channel_id"] == "C1"
    assert pages[0][0]["_channel_name"] == "general"
    assert pages[1][0]["_channel_id"] == "C2"


async def test_slack_fetch_raw_skips_channels_with_no_history(mocker, slack_config):
    adapter = SlackAdapter(slack_config)

    async def fake_paginate_pages(*args, **kwargs):
        yield [{"id": "C1", "name": "general"}, {"id": "C2", "name": "empty"}]

    mocker.patch.object(
        adapter.client, "paginate_pages", new=MagicMock(side_effect=fake_paginate_pages)
    )
    mocker.patch.object(
        adapter.client,
        "paginated_get",
        new=AsyncMock(side_effect=[[{"ts": "1.1", "text": "hi"}], []]),
    )

    pages = [page async for page in adapter.fetch_raw()]

    assert len(pages) == 1
    assert pages[0][0]["_channel_id"] == "C1"


# --- normalize() ---
def test_slack_normalize_rich_message(slack_config):
    adapter = SlackAdapter(slack_config)
    raw = [
        {
            "type": "message",
            "ts": "1704067200.000100",
            "text": "Hello world",
            "user": "U123",
            "_channel_id": "C123",
            "_channel_name": "general",
        }
    ]
    assets = adapter.normalize(raw)
    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].asset_id == "C123_1704067200.000100"
    assert assets[0].name == "Hello world"
    assert assets[0].last_seen == datetime.fromtimestamp(1704067200.0001, tz=timezone.utc)


def test_slack_normalize_empty_text_uses_fallback(slack_config):
    adapter = SlackAdapter(slack_config)
    raw = [
        {
            "type": "message",
            "subtype": "file_share",
            "ts": "1704067200.000200",
            "text": "",
            "_channel_id": "C123",
            "_channel_name": "general",
        }
    ]
    assets = adapter.normalize(raw)
    assert assets[0].name == "(no text - file_share)"
