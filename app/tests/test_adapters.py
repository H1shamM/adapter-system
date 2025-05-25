import pytest
from app.adapters.factory import get_adapter
from app.adapters.github_adapter.adapter import GitHubAdapter


def test_github_adapter():
    config = {
        "name": "github-prod",
        "token": "ghp_testtoken",
        "org": "axios",
        "repo": "axios"
    }
    adapter = get_adapter("github", config)
    assert adapter.connect() is False  # Invalid token

def test_adapter_creation():
    # Test adapter creation
    adapter = get_adapter("github", {
        "name": "gh-prod",
        "token": "ghp_test",
        "org": "axios",
        "repo": "axios"
    })
    assert isinstance(adapter, GitHubAdapter)


def test_mock_adapter_normalization():
    config = {
        "name": "mock-test",
        "num_assets": 5
    }
    adapter = get_adapter("mock", config)
    raw = adapter.fetch_raw()
    normalized = adapter.normalize(raw)
    assert len(normalized) == 5
    assert "asset_id" in normalized[0]