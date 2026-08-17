from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Literal, Optional, Type

import httpx
from pydantic import Field

from app.adapters.errors import AuthenticationError, FetchError
from app.http.client import AssetHttpClient, HttpClientConfig
from app.models.assets import NormalizedAsset


class AdapterConfig(HttpClientConfig):  # Inherit from HttpClientConfig
    """Combines HTTP config with adapter-specific settings"""

    name: str = Field(..., min_length=3)
    enabled: bool = True

    sync_interval: int = Field(3600, ge=60)
    priority: Literal["low", "medium", "high"] = "medium"

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
    def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """Yield raw vendor data in chunks -- one chunk for adapters with bounded results
        (nothing to gain from chunking a dataset that already fits in memory), one chunk per
        page for adapters whose result set can be unbounded (paginated APIs, enterprise fleets),
        so storage can happen incrementally instead of after everything is fetched. Declared
        without `async` (mypy-correct for an async-generator-returning method: calling an async
        generator function is itself synchronous, it doesn't return a coroutine -- only
        `__anext__` on the result is awaited) -- concrete overrides are `async def ... : yield`,
        real async generator functions, which satisfy this signature."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        """Convert one chunk to the unified schema"""
        pass

    async def stream(self) -> AsyncIterator[List[NormalizedAsset]]:
        """connect() + fetch_raw()/normalize() per chunk, with error translation -- the one
        production entrypoint (sync_engine.run_adapter_sync drains this directly, chunk by
        chunk). Not every adapter's connect() self-translates raw HTTP errors into
        AuthenticationError/FetchError (some rely entirely on this wrapper), so this has to be
        the one place both this and execute() go through."""
        try:
            await self.connect()
            async for chunk in self.fetch_raw():
                yield self.normalize(chunk)
        except AuthenticationError:
            raise
        except httpx.HTTPStatusError as err:
            if err.response.status_code in (401, 403):
                raise AuthenticationError(f"Authentication failed: {str(err)}") from err
            raise FetchError(
                f"{self.config.name}: execution failed ({err.response.status_code})"
            ) from err
        except Exception as e:
            raise FetchError(f"{self.config.name}: execution failed") from e

    async def execute(self) -> List[NormalizedAsset]:
        """Drains stream() into one list -- for callers that want the whole batch at once (CLI
        runs, tests)."""
        assets: List[NormalizedAsset] = []
        async for chunk in self.stream():
            assets.extend(chunk)
        return assets

    async def close(self):
        """Close connection"""
        await self.client.close()
