"""respx-based tests for GitHubIssueClient (app/integrations/github.py) -- mocks httpx at the
TRANSPORT layer, same convention as app/tests/adapters/test_crowdstrike_adapter_mock_endpoints.py,
so the real request-building code (headers, params, URL, JSON body) actually runs against
realistic GitHub REST API response shapes, not just the drift watcher's mocked collaborator.
"""

import respx
from httpx import Response

from app.config import settings
from app.integrations.github import GitHubIssueClient

BASE = "https://api.github.com/repos/acme/adapter-system"


@respx.mock
async def test_find_open_drift_issue_matches_by_title(mocker):
    mocker.patch.object(settings.github, "repo", "acme/adapter-system")
    route = respx.get(f"{BASE}/issues", params={"labels": "adapter-drift", "state": "open"}).mock(
        return_value=Response(
            200,
            json=[
                {"number": 5, "title": "[adapter-drift] other-adapter (slack) failing repeatedly"},
                {
                    "number": 7,
                    "title": "[adapter-drift] crowdstrike-prod (crowdstrike) failing repeatedly",
                },
            ],
        )
    )

    client = GitHubIssueClient()
    issue_number = await client.find_open_drift_issue("crowdstrike-prod")

    assert issue_number == 7
    assert route.called


@respx.mock
async def test_find_open_drift_issue_skips_pull_requests(mocker):
    mocker.patch.object(settings.github, "repo", "acme/adapter-system")
    respx.get(f"{BASE}/issues", params={"labels": "adapter-drift", "state": "open"}).mock(
        return_value=Response(
            200,
            json=[
                {
                    "number": 3,
                    "title": "[adapter-drift] crowdstrike-prod backport",
                    "pull_request": {"url": "..."},
                }
            ],
        )
    )

    client = GitHubIssueClient()
    issue_number = await client.find_open_drift_issue("crowdstrike-prod")

    assert issue_number is None


@respx.mock
async def test_find_open_drift_issue_returns_none_when_no_match(mocker):
    mocker.patch.object(settings.github, "repo", "acme/adapter-system")
    respx.get(f"{BASE}/issues", params={"labels": "adapter-drift", "state": "open"}).mock(
        return_value=Response(200, json=[])
    )

    client = GitHubIssueClient()
    assert await client.find_open_drift_issue("crowdstrike-prod") is None


@respx.mock
async def test_create_drift_issue_posts_title_body_and_label(mocker):
    mocker.patch.object(settings.github, "repo", "acme/adapter-system")
    route = respx.post(f"{BASE}/issues").mock(return_value=Response(201, json={"number": 42}))

    client = GitHubIssueClient()
    issue_number = await client.create_drift_issue(
        adapter_id="crowdstrike-prod",
        adapter_type="crowdstrike",
        evidence=[
            {"sync_id": "s1", "finished_at": "2026-08-17T00:00:00Z", "error": "401 Unauthorized"}
        ],
    )

    assert issue_number == 42
    request_body = route.calls[0].request.content.decode()
    assert "crowdstrike-prod" in request_body
    assert "adapter-drift" in request_body
    assert "401 Unauthorized" in request_body
