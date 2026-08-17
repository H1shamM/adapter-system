"""Regression coverage for AssetHttpClient.paginate_pages() / gather_bounded(), added when
introducing per-page streaming (see BaseAdapter.stream()). Uses respx to mock httpx at the
transport layer, same pattern as test_crowdstrike_adapter_mock_endpoints.py, so the real
request/pagination code is what's actually exercised.
"""

import asyncio

import respx
from httpx import Response

from app.http.client import AssetHttpClient, HttpClientConfig

BASE = "https://example.test"


def _client() -> AssetHttpClient:
    config = HttpClientConfig(base_url=BASE, auth_type="none")
    return AssetHttpClient(config, "test-adapter")


@respx.mock
async def test_paginate_pages_yields_each_page_separately():
    respx.get(f"{BASE}/items").mock(
        side_effect=[
            Response(200, json={"items": [1, 2]}),
            Response(200, json={"items": [3]}),
        ]
    )
    client = _client()
    try:
        pages = [
            page
            async for page in client.paginate_pages(
                "/items", pagination="page_number", page_size=2, extract_data=lambda r: r["items"]
            )
        ]
    finally:
        await client.close()

    assert pages == [[1, 2], [3]]


@respx.mock
async def test_paginated_get_returns_flattened_equivalent_of_paginate_pages():
    respx.get(f"{BASE}/items").mock(
        side_effect=[
            Response(200, json={"items": [1, 2]}),
            Response(200, json={"items": [3]}),
        ]
    )
    client = _client()
    try:
        result = await client.paginated_get(
            "/items", pagination="page_number", page_size=2, extract_data=lambda r: r["items"]
        )
    finally:
        await client.close()

    assert result == [1, 2, 3]


@respx.mock
async def test_paginate_pages_cursor_body_stops_when_no_offset():
    """Same cursor_body mechanics CrowdStrike's stream() relies on -- generalized field
    path/param name, not hardcoded to Slack's response_metadata.next_cursor shape."""
    respx.get(f"{BASE}/resources").mock(
        side_effect=[
            Response(
                200,
                json={"resources": ["a", "b"], "meta": {"pagination": {"offset": "next-token"}}},
            ),
            Response(200, json={"resources": ["c"], "meta": {"pagination": {}}}),
        ]
    )
    client = _client()
    try:
        pages = [
            page
            async for page in client.paginate_pages(
                "/resources",
                pagination="cursor_body",
                cursor_response_path="meta.pagination.offset",
                cursor_param_name="offset",
                extract_data=lambda r: r["resources"],
            )
        ]
    finally:
        await client.close()

    assert pages == [["a", "b"], ["c"]]


async def test_gather_bounded_respects_concurrency_limit():
    client = _client()
    in_flight = 0
    max_in_flight = 0
    lock = asyncio.Lock()

    async def task():
        nonlocal in_flight, max_in_flight
        async with lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.01)
        async with lock:
            in_flight -= 1
        return "done"

    try:
        results = await client.gather_bounded([task() for _ in range(10)], limit=3)
    finally:
        await client.close()

    assert results == ["done"] * 10
    assert max_in_flight <= 3


async def test_gather_bounded_propagates_exceptions():
    client = _client()

    async def boom():
        raise ValueError("bad")

    try:
        with_raise = client.gather_bounded([boom()], limit=1)
        try:
            await with_raise
        except ValueError as e:
            assert str(e) == "bad"
        else:
            raise AssertionError("expected ValueError to propagate")
    finally:
        await client.close()
