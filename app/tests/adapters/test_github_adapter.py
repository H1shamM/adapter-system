import pytest
from requests import HTTPError

from app.adapters.errors import AuthenticationError, FetchError
from app.adapters.github_adapter.adapter import GitHubAdapter, GitHubConfig
from app.models.assets import NormalizedAsset


@pytest.fixture
def github_config():
    return GitHubConfig(
        name="github",
        base_url="https://api.github.com",
        auth_type="bearer",
        auth_config={"token": "test-token"},
        repo="axios/axios",
    )


class FakeResponse:
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status_code = status
        self.headers = {"content-type": "application/json"}

    def json(self):
        return self._json


def test_github_adapter(mocker, github_config: GitHubConfig):
    adapter = GitHubAdapter(github_config)

    mocker.patch.object(adapter, "connect", return_value=True)

    mocker.patch.object(
        adapter,
        "fetch_raw",
        return_value=[
            {
                "id": 1,
                "title": "bug",
                "state": "open",
                "updated_at": "2024-01-01 00:00:00",
                "html_url": "https://github.com/axios/axios",
                "labels": []

            }
        ]
    )

    assets = adapter.execute()

    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].vendor == "GitHub"


def test_github_adapter_fetch_unauthorized(mocker, github_config: GitHubConfig):
    adapter = GitHubAdapter(github_config)

    mocker.patch.object(adapter, "connect", return_value=True)

    mocker.patch.object(
        adapter.client,
        "paginated_get",
        side_effect= HTTPError()
    )

    with pytest.raises(FetchError):
        adapter.execute()

def test_github_adapter_auth_failure(mocker, github_config: GitHubConfig):
    adapter = GitHubAdapter(github_config)

    mocker.patch.object(adapter, "connect", return_value=False)

    with pytest.raises(AuthenticationError):
        adapter.execute()


def test_github_normalization(github_config: GitHubConfig):
    adapter = GitHubAdapter(github_config)

    raw = [{
        "id": 2,
        "title": "Feature",
        "state": "closed",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/axios/axios",
        "labels": [{"name": "enhancement"}]
    }]

    assets = adapter.normalize(raw)

    assert assets[0].status == "CLOSED"
    assert assets[0].metadata['labels'] == ["enhancement"]
