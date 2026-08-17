"""Unit tests for check_repeatedly_failing_adapters (app/tasks/scheduler.py).

Mocks AdapterConfigStore, SyncHistoryStore, and GitHubIssueClient -- fast, deterministic, no
network/Mongo/GitHub calls. This is the guardrail-in-code test: the failure-streak threshold and
the dedupe-before-creating-a-second-issue check are plain Python conditionals, and this asserts
they actually gate correctly, not just that the happy path works (the same lesson quest4-agents'
min-2-tool-calls guardrail test applies).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def patched_watcher(mocker):
    fake_adapter_store = MagicMock()
    mocker.patch("app.tasks.scheduler.AdapterConfigStore", return_value=fake_adapter_store)

    fake_history_store = MagicMock()
    mocker.patch("app.tasks.scheduler.SyncHistoryStore", return_value=fake_history_store)

    fake_github = MagicMock()
    fake_github.find_open_drift_issue = AsyncMock(return_value=None)
    fake_github.create_drift_issue = AsyncMock(return_value=42)
    mocker.patch("app.tasks.scheduler.GitHubIssueClient", return_value=fake_github)

    return {
        "adapter_store": fake_adapter_store,
        "history_store": fake_history_store,
        "github": fake_github,
    }


def _adapter(adapter_id="a1", adapter_type="crowdstrike", enabled=True):
    return {"adapter_id": adapter_id, "adapter_type": adapter_type, "enabled": enabled}


def test_opens_issue_when_streak_at_threshold(patched_watcher):
    patched_watcher["adapter_store"].list_all.return_value = [_adapter()]
    patched_watcher["history_store"].last_n_statuses.return_value = ["FAILED", "FAILED", "FAILED"]
    patched_watcher["history_store"].list.return_value = [{"sync_id": "s1", "error": "boom"}]

    from app.tasks.scheduler import check_repeatedly_failing_adapters

    result = check_repeatedly_failing_adapters()

    patched_watcher["github"].create_drift_issue.assert_awaited_once_with(
        adapter_id="a1", adapter_type="crowdstrike", evidence=[{"sync_id": "s1", "error": "boom"}]
    )
    assert result == {"checked": 1, "flagged": 1, "timestamp": result["timestamp"]}


def test_does_not_fire_below_threshold(patched_watcher):
    patched_watcher["adapter_store"].list_all.return_value = [_adapter()]
    # only 2 statuses returned -- fewer than FAILURE_STREAK_THRESHOLD (3)
    patched_watcher["history_store"].last_n_statuses.return_value = ["FAILED", "FAILED"]

    from app.tasks.scheduler import check_repeatedly_failing_adapters

    result = check_repeatedly_failing_adapters()

    patched_watcher["github"].create_drift_issue.assert_not_awaited()
    assert result["flagged"] == 0


def test_does_not_fire_when_streak_has_a_success(patched_watcher):
    patched_watcher["adapter_store"].list_all.return_value = [_adapter()]
    patched_watcher["history_store"].last_n_statuses.return_value = [
        "FAILED",
        "SUCCESS",
        "FAILED",
    ]

    from app.tasks.scheduler import check_repeatedly_failing_adapters

    result = check_repeatedly_failing_adapters()

    patched_watcher["github"].create_drift_issue.assert_not_awaited()
    assert result["flagged"] == 0


def test_does_not_duplicate_an_already_open_issue(patched_watcher):
    patched_watcher["adapter_store"].list_all.return_value = [_adapter()]
    patched_watcher["history_store"].last_n_statuses.return_value = ["FAILED", "FAILED", "FAILED"]
    patched_watcher["github"].find_open_drift_issue = AsyncMock(return_value=17)

    from app.tasks.scheduler import check_repeatedly_failing_adapters

    result = check_repeatedly_failing_adapters()

    patched_watcher["github"].create_drift_issue.assert_not_awaited()
    assert result["flagged"] == 0


def test_skips_disabled_adapters(patched_watcher):
    patched_watcher["adapter_store"].list_all.return_value = [_adapter(enabled=False)]

    from app.tasks.scheduler import check_repeatedly_failing_adapters

    result = check_repeatedly_failing_adapters()

    patched_watcher["history_store"].last_n_statuses.assert_not_called()
    assert result == {"checked": 0, "flagged": 0, "timestamp": result["timestamp"]}


def test_one_adapters_error_does_not_stop_the_rest(patched_watcher):
    patched_watcher["adapter_store"].list_all.return_value = [
        _adapter(adapter_id="broken"),
        _adapter(adapter_id="fine"),
    ]
    patched_watcher["history_store"].last_n_statuses.side_effect = [
        RuntimeError("mongo blip"),
        ["FAILED", "FAILED", "FAILED"],
    ]
    patched_watcher["history_store"].list.return_value = [{"sync_id": "s1", "error": "boom"}]

    from app.tasks.scheduler import check_repeatedly_failing_adapters

    result = check_repeatedly_failing_adapters()

    assert result == {"checked": 2, "flagged": 1, "timestamp": result["timestamp"]}
    patched_watcher["github"].create_drift_issue.assert_awaited_once()
