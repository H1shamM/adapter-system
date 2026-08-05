from app.adapters.auth0.adapter import Auth0Adapter
from app.adapters.auth0.config import Auth0Config
from app.adapters.aws.adapter import AWSAdapter, AWSConfig
from app.adapters.base import AdapterConfig, BaseAdapter
from app.adapters.coingecko.adapter import CoinGeckoAdapter
from app.adapters.crowdstrike.adapter import CrowdStrikeAdapter
from app.adapters.crowdstrike.config import CrowdStrikeConfig
from app.adapters.github_adapter.adapter import GitHubAdapter, GitHubConfig
from app.adapters.JSONPlaceholder.adapter import JSONPlaceholderAdapter
from app.adapters.mock_adapter.adapter import MockAdapter, MockConfig
from app.adapters.perf_test.adapter import PerfTestAdapter, PerfTestConfig
from app.adapters.random_user.adapter import RandomUserAdapter
from app.adapters.slack.adapter import SlackAdapter
from app.adapters.slack.config import SlackConfig

ADAPTER_REGISTRY = {
    "github": (GitHubAdapter, GitHubConfig),
    "aws": (AWSAdapter, AWSConfig),
    "mock": (MockAdapter, MockConfig),
    "jsonplaceholder": (JSONPlaceholderAdapter, AdapterConfig),
    "coingecko": (CoinGeckoAdapter, AdapterConfig),
    "randomuser": (RandomUserAdapter, AdapterConfig),
    "perftest": (PerfTestAdapter, PerfTestConfig),
    "auth0": (Auth0Adapter, Auth0Config),
    "slack": (SlackAdapter, SlackConfig),
    "crowdstrike": (CrowdStrikeAdapter, CrowdStrikeConfig),
}


def build_adapter(adapter_type: str, config: dict) -> BaseAdapter:
    adapter_class, config_class = ADAPTER_REGISTRY[adapter_type]
    validated_config = config_class(**config)
    return adapter_class(validated_config)
