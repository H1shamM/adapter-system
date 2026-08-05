import asyncio
import os
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import httpx
from httpx_aws_auth import AwsCredentials, AwsSigV4Auth
from prometheus_client import Counter, Gauge
from pydantic import BaseModel, Field

from app.adapters.registry import AuthType
from app.config import settings

# Metrics setup
REQUEST_COUNTER = Counter(
    "adapter_http_requests_total",
    "Total API requests by adapter and status",
    ["adapter", "method", "status"],
)

RATE_LIMIT_GAUGE = Gauge("adapter_rate_limit_remaining", "Remaining API rate limit", ["adapter"])


class HttpClientConfig(BaseModel):
    """Configuration for an HTTP client"""

    base_url: str
    auth_type: AuthType = "none"
    auth_config: Dict[str, Any] = Field(default_factory=dict)

    default_timeout: int = Field(default=settings.client.default_timeout)
    max_retries: int = Field(default=settings.client.default_max_retries)
    retry_wait: int = Field(default=settings.client.default_retry_wait)

    max_connections: int = 100
    max_keepalive_connections: int = 20


class AssetHttpClient:
    def __init__(self, config: HttpClientConfig, adapter_name: str):
        self.config = config
        self.adapter_name = adapter_name
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(connect=5, read=config.default_timeout, write=10, pool=5),
        )
        self._setup_auth()

    def _setup_auth(self):
        """Configure authentication based on type"""
        auth_type = self.config.auth_type

        if auth_type == "bearer":
            token = self._resolve_secret(self.config.auth_config.get("token"))
            self.client.headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "aws_sigv4":
            credentials = AwsCredentials(
                access_key=self._resolve_secret(self.config.auth_config["access_key"]),
                secret_key=self._resolve_secret(self.config.auth_config["secret_key"]),
            )
            self.client.auth = AwsSigV4Auth(
                credentials,
                self._resolve_secret(self.config.auth_config["region"]),
                "execute-api",
            )

        elif auth_type == "api_key":
            key = self._resolve_secret(self.config.auth_config["key"])
            header = self.config.auth_config.get("header", "X-API-KEY")
            self.client.headers[header] = key

        elif auth_type == "oauth2_client_credentials":
            # client_id/client_secret/token_url are always required. audience and grant_type are
            # OPTIONAL -- Auth0 needs both (JSON body); CrowdStrike needs neither, just
            # client_id/client_secret, form-encoded. Resolving only what's actually present avoids
            # forcing every future oauth2_client_credentials vendor into Auth0's exact shape.
            for key in ("client_id", "client_secret", "audience", "grant_type"):
                if key in self.config.auth_config:
                    self.config.auth_config[key] = self._resolve_secret(
                        self.config.auth_config[key]
                    )
            self.config.auth_config["token_url"] = self._resolve_secret(
                self.config.auth_config["token_url"]
            )
            self._token = None
            self._token_expires_at = 0

    def _resolve_secret(self, value: Any):
        """
        Resolve a value ,checking if it's an env variable reference
        """
        if isinstance(value, str) and value.startswith("VAR:"):
            env_name = value[4:]
            return os.getenv(env_name, "")
        return value

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Core request method with retry logic"""
        if path.startswith("http://") or path.startswith("https://"):
            full_url = path
        else:
            full_url = f"{self.config.base_url}{path}"

        # Set default timeout
        kwargs.setdefault("timeout", self.config.default_timeout)
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.request(method, full_url, **kwargs)
                response.raise_for_status()
                # Track metrics
                REQUEST_COUNTER.labels(
                    adapter=self.adapter_name, method=method.upper(), status="success"
                ).inc()

                # Track rate limits
                if "X-RateLimit-Remaining" in response.headers:
                    RATE_LIMIT_GAUGE.labels(adapter=self.adapter_name).set(
                        int(response.headers["X-RateLimit-Remaining"])
                    )

                return response

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                REQUEST_COUNTER.labels(
                    adapter=self.adapter_name, method=method.upper(), status=f"error_{status_code}"
                ).inc()

                if status_code in (401, 403):
                    raise

                if attempt == self.config.max_retries - 1:
                    raise

                await asyncio.sleep(self.config.retry_wait)

            except httpx.RequestError:
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(self.config.retry_wait)

    # Convenience methods
    async def get(self, path: str, **kwargs):
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.request("POST", path, **kwargs)

    async def paginated_get(
        self,
        path: str,
        params: Optional[Dict] = None,
        pagination: str = "link_header",  # 'link_header' | 'page_number' | 'offset' | 'cursor_body'
        page_size: int = 100,
        max_pages: int = 100,
        extract_data: Callable[[Dict], List] = lambda r: r["items"],
        get_next_page: Optional[Callable[[httpx.Response], Optional[Dict]]] = None,
        cursor_response_path: str = "response_metadata.next_cursor",
        cursor_param_name: str = "cursor",
    ) -> List[Dict]:
        """
        Fetch paginated resources automatically. cursor_response_path/cursor_param_name only
        apply to pagination="cursor_body" -- the cursor's location in the response body and the
        request param it's echoed back as both vary per vendor (Slack: response_metadata.
        next_cursor -> "cursor"; CrowdStrike: meta.pagination.offset -> "offset"), even though the
        underlying shape (cursor lives in the body, not a header or a client-computed number) is
        the same across both.
        """

        results = []
        current_page = 1
        next_params = params.copy() if params else {}
        url: Optional[str] = None

        while current_page <= max_pages:

            if url:
                parsed = urlparse(url)
                path = parsed.path
                next_params = parse_qs(parsed.query)
                response = await self.get(path, params=next_params)
            else:
                response = await self.get(path, params=next_params)

            # Extract data using provided function
            page_data = extract_data(response.json())
            results.extend(page_data)

            # Get next page parameters
            next_page_params = self._get_next_page_params(
                response,
                pagination,
                current_page,
                page_size,
                len(page_data),
                cursor_response_path,
                cursor_param_name,
            )

            # Custom next page handler
            if get_next_page:
                next_info = get_next_page(response)
                if not next_info:
                    break
                url = next_info.get("url")
                next_params = next_info.get("params", {})
                continue

            # Stop if no more pages
            if not next_page_params:
                break

            if pagination in ("link_header", "cursor_body"):
                next_params = next_page_params
                current_page += 1
                continue

            # Prepare the next request
            if pagination == "page_number":
                current_page += 1
                next_params["page"] = current_page
            elif pagination == "offset":
                next_params["offset"] = len(results)

            url = None  # Reset URL for param-based pagination

        return results

    def _get_next_page_params(
        self,
        response: httpx.Response,
        strategy: str,
        current_page: int,
        page_size: int,
        page_data_len: int = 0,
        cursor_response_path: str = "response_metadata.next_cursor",
        cursor_param_name: str = "cursor",
    ) -> Optional[Dict]:
        """
        Determine parameters for next page request
        """

        if strategy == "cursor_body":
            # Cursor lives in the response BODY, not a Link header or a client-computed
            # page/offset -- but WHERE in the body and what it's called on the next request both
            # vary per vendor (see paginated_get's docstring), so both are parameterized.
            value = response.json()
            for key in cursor_response_path.split("."):
                value = value.get(key) if isinstance(value, dict) else None
                if value is None:
                    break
            if value:
                return {cursor_param_name: value}
            return None
        elif strategy == "link_header":
            link_header = response.headers.get("Link", "")
            if 'rel="next"' in link_header:
                next_url = None
                for link in link_header.split(","):
                    if 'rel="next"' in link:
                        next_url = link.split(";")[0].strip("<> ")
                        break
                if next_url:
                    parsed = urlparse(next_url)
                    return parse_qs(parsed.query)
        elif strategy == "page_number":
            # Stop once a page comes back with fewer than a full page of results --
            # otherwise this walks forever (up to max_pages) regardless of real data,
            # which is what let it walk past Auth0's actual 1000-record paging limit.
            if page_data_len < page_size:
                return None
            return {"page": current_page + 1, "per_page": page_size}
        elif strategy == "offset":
            content = response.json()
            if len(content.get("items", [])) < page_size:
                return None
            return {"offset": content.get("offset", 0) + page_size}

        return None

    async def ensure_token(self):
        if self._token and time.time() < self._token_expires_at - 60:  # 60s safety margin
            return

        # Build the payload from whatever's actually present in auth_config, rather than
        # hardcoding Auth0's exact 4-key shape -- CrowdStrike's client-credentials grant only
        # wants client_id/client_secret. token_body_format picks JSON (Auth0's shape) vs
        # form-encoded (CrowdStrike's shape); httpx form-encodes a dict passed via `data=`.
        payload = {
            "client_id": self.config.auth_config["client_id"],
            "client_secret": self.config.auth_config["client_secret"],
        }
        for optional_key in ("grant_type", "audience"):
            if optional_key in self.config.auth_config:
                payload[optional_key] = self.config.auth_config[optional_key]

        body_format = self.config.auth_config.get("token_body_format", "json")
        request_kwargs = {"json": payload} if body_format == "json" else {"data": payload}

        resp = await self.request("POST", self.config.auth_config["token_url"], **request_kwargs)
        body = resp.json()
        token = body.get("access_token")
        self._token = token
        self._token_expires_at = time.time() + body.get("expires_in", 0)
        if not token:
            raise ValueError("oauth2_client_credentials: token response had no access_token")
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
