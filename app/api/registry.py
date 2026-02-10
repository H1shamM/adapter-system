from app.adapters.aws.adapter import AWSConfig
from app.adapters.base import AdapterConfig
from app.adapters.github_adapter.adapter import GitHubConfig
from app.adapters.mock_adapter.adapter import MockConfig

ADAPTER_CONFIGS = {
    "github": GitHubConfig,
    "aws": AWSConfig,
    "mock":  MockConfig,
    "jsonplaceholder":  AdapterConfig,
    "coingecko": AdapterConfig,
    "randomuser": AdapterConfig,
}