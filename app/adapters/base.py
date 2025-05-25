from abc import ABC, abstractmethod
from pydantic import Field
from typing import Dict, List, Optional, Literal, Type

from app.http.client import HttpClientConfig, AssetHttpClient
from app.models.assets import NormalizedAsset


class AdapterConfig(HttpClientConfig):  # Inherit from HttpClientConfig
    """Combines HTTP config with adapter-specific settings"""
    name: str = Field(..., min_length=3)
    enabled: bool = True
    sync_interval: int = Field(3600, ge=60)  # Minimum 60 seconds
    priority: Literal['low', 'medium', 'high'] = 'medium'
    asset_types: List[str] = []  # Types this adapter handles



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
    def connect(self) -> bool:
        """Test credentials/connection"""
        pass

    @abstractmethod
    def fetch_raw(self) -> List[Dict]:
        """Get raw vendor data"""
        pass

    @abstractmethod
    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        """Convert to unified schema"""
        pass

    def execute(self) -> List[NormalizedAsset]:
        """Full execution flow"""
        if not self.connect():
            raise ConnectionError("Adapter connection failed")
        raw = self.fetch_raw()
        return self.normalize(raw)