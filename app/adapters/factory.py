from app.adapters.aws.adapter import AWSAdapter, AWSConfig
from app.adapters.base import BaseAdapter
from app.adapters.github_adapter.adapter import GitHubAdapter, GitHubConfig
from app.adapters.mock_adapter.adapter import MockAdapter, MockConfig

ADAPTER_REGISTRY = {
    "github": (GitHubAdapter, GitHubConfig),
    "aws": (AWSAdapter, AWSConfig),
    "mock": (MockAdapter, MockConfig)
}

def get_adapter(adapter_type: str, config: dict) -> BaseAdapter:
    adapter_class, config_class = ADAPTER_REGISTRY[adapter_type]
    validated_config = config_class(**config)
    return adapter_class(validated_config)