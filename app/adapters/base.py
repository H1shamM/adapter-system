from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Literal, Type

from pydantic import Field

from app.adapters.errors import AuthenticationError, FetchError
from app.http.client import HttpClientConfig, AssetHttpClient
from app.models.assets import NormalizedAsset


class AdapterConfig(HttpClientConfig):  # Inherit from HttpClientConfig
    """Combines HTTP config with adapter-specific settings"""
    name: str = Field(..., min_length=3)
    enabled: bool = True

    sync_interval: int = Field(3600, ge=60)
    priority: Literal['low', 'medium', 'high'] = 'medium'

    asset_types: List[str] = Field(default_factory=list)


class BaseAdapter(ABC):
    HTTP_CONFIG_CLASS: Type[AdapterConfig] = HttpClientConfig

    def __init__(self, config: AdapterConfig):
        self.config = config  # Store full config
        self.http_client = AssetHttpClient(config, self.__class__.__name__)
        self._last_sync: Optional[float] = None

    @property
    def client(self):
        """Shortcut to an HTTP client"""
        return self.http_client

    @abstractmethod
    async def connect(self):
        """Test credentials/connection"""
        pass

    @abstractmethod
    async def fetch_raw(self) -> List[Dict]:
        """Get raw vendor data"""
        pass

    @abstractmethod
    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        """Convert to unified schema"""
        pass

    async def execute(self) -> List[NormalizedAsset]:
        """Full execution flow"""
        try:
            await self.connect()
            raw_data = await self.fetch_raw()
            return self.normalize(raw_data)
        except AuthenticationError:
            raise
        except Exception as e:
            raise FetchError(
                f"{self.config.name}: execution failed"
            ) from e

    async def close(self):
        """Close connection"""
        await self.client.close()
