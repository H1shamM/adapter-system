from app.adapters.JSONPlaceholder.adapter import JSONPlaceholderAdapter
from app.adapters.aws.adapter import AWSAdapter, AWSConfig
from app.adapters.base import BaseAdapter, AdapterConfig
from app.adapters.coingecko.adapter import CoinGeckoAdapter
from app.adapters.github_adapter.adapter import GitHubAdapter, GitHubConfig
from app.adapters.mock_adapter.adapter import MockAdapter, MockConfig
from app.adapters.random_user.adapter import RandomUserAdapter

ADAPTER_REGISTRY = {
    "github": (GitHubAdapter, GitHubConfig),
    "aws": (AWSAdapter, AWSConfig),
    "mock": (MockAdapter, MockConfig),
    "jsonplaceholder": (JSONPlaceholderAdapter, AdapterConfig),
    "coingecko": (CoinGeckoAdapter, AdapterConfig),
    "randomuser": (RandomUserAdapter, AdapterConfig),
}


def build_adapter(adapter_type: str, config: dict) -> BaseAdapter:
    adapter_class, config_class = ADAPTER_REGISTRY[adapter_type]
    validated_config = config_class(**config)
    return adapter_class(validated_config)
