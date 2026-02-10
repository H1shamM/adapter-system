import time
from typing import Optional, Dict, Any, Callable, List
from urllib.parse import urlparse, parse_qs

import requests
from prometheus_client import Counter, Gauge
from pydantic import BaseModel, Field
from requests.exceptions import HTTPError

from app.adapters.registry import AuthType

# Metrics setup
REQUEST_COUNTER = Counter(
    'adapter_http_requests_total',
    'Total API requests by adapter and status',
    ['adapter', 'method', 'status']
)

RATE_LIMIT_GAUGE = Gauge(
    'adapter_rate_limit_remaining',
    'Remaining API rate limit',
    ['adapter']
)


class HttpClientConfig(BaseModel):
    """Configuration for an HTTP client"""
    base_url: str
    auth_type: AuthType = "none"
    auth_config: Dict[str, Any] = Field(default_factory=dict)

    default_timeout: int = 30
    max_retries: int = 3
    retry_wait: int = 5


class AssetHttpClient:
    def __init__(self, config: HttpClientConfig, adapter_name: str):
        self.config = config
        self.adapter_name = adapter_name
        self.session = requests.Session()
        self._setup_auth()

    def _setup_auth(self):
        """Configure authentication based on type"""
        auth_type = self.config.auth_type

        if auth_type == "bearer":
            token = self.config.auth_config.get("token")
            self.session.headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "aws_sigv4":
            from requests_aws4auth import AWS4Auth
            self.session.auth = AWS4Auth(
                self.config.auth_config["access_key"],
                self.config.auth_config["secret_key"],
                self.config.auth_config["region"],
                "execute-api"  # Service name for AWS APIs
            )

        elif auth_type == "api_key":
            key = self.config.auth_config["key"]
            header = self.config.auth_config.get("header", "X-API-KEY")
            self.session.headers[header] = key

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Core request method with retry logic"""
        full_url = f"{self.config.base_url}{path}"

        # Set default timeout
        kwargs.setdefault("timeout", self.config.default_timeout)
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.request(method, full_url, **kwargs)
                response.raise_for_status()
                # Track metrics
                REQUEST_COUNTER.labels(
                    adapter=self.adapter_name,
                    method=method.upper(),
                    status="success"
                ).inc()

                # Track rate limits
                if 'X-RateLimit-Remaining' in response.headers:
                    RATE_LIMIT_GAUGE.labels(adapter=self.adapter_name).set(
                        int(response.headers['X-RateLimit-Remaining'])
                    )

                return response

            except HTTPError as e:
                status_code = e.response.status_code
                REQUEST_COUNTER.labels(
                    adapter=self.adapter_name,
                    method=method.upper(),
                    status=f"error_{status_code}"
                ).inc()

                if status_code in (401, 403):
                    raise

                if attempt == self.config.max_retries - 1:
                    raise
                # Handle rate limits
                # if e.response.status_code == 429:
                #     retry_after = e.response.headers.get('Retry-After', 60)
                #     time.sleep(int(retry_after))
                time.sleep(self.config.retry_wait)

    # Convenience methods
    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def paginated_get(
            self,
            path: str,
            params: Optional[Dict] = None,
            pagination: str = 'link_header',  # 'link_header' | 'page_number' | 'offset'
            page_size: int = 100,
            max_pages: int = 100,
            extract_data: Callable[[Dict], List] = lambda r: r['items'],
            get_next_page: Optional[Callable[[requests.Response], Optional[Dict]]] = None
    ) -> List[Dict]:
        """
        Fetch paginated resources automatically
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
                response = self.get(path, params=next_params)
            else:
                response = self.get(path, params=next_params)

            # Extract data using provided function
            page_data = extract_data(response.json())
            results.extend(page_data)

            # Get next page parameters
            next_page_params = self._get_next_page_params(
                response,
                pagination,
                current_page,
                page_size
            )



            # Custom next page handler
            if get_next_page:
                next_info = get_next_page(response)
                if not next_info:
                    break
                url = next_info.get('url')
                next_params = next_info.get('params', {})
                continue

            # Stop if no more pages
            if not next_page_params:
                break


            if pagination == 'link_header':
                next_params = next_page_params
                current_page += 1
                continue

            # Prepare the next request
            if pagination == 'page_number':
                current_page += 1
                next_params['page'] = current_page
            elif pagination == 'offset':
                next_params['offset'] = len(results)

            url = None  # Reset URL for param-based pagination

        return results

    def _get_next_page_params(
            self,
            response: requests.Response,
            strategy: str,
            current_page: int,
            page_size: int
    ) -> Optional[Dict]:
        """
        Determine parameters for next page request
        """

        if strategy == 'link_header':
            link_header = response.headers.get('Link', '')
            if 'rel="next"' in link_header:
                next_url = None
                for link in link_header.split(','):
                    if 'rel="next"' in link:
                        next_url = link.split(';')[0].strip('<> ')
                        break
                if next_url:
                    parsed = urlparse(next_url)
                    return parse_qs(parsed.query)
        elif strategy == 'page_number':
            return {'page': current_page + 1, 'per_page': page_size}
        elif strategy == 'offset':
            content = response.json()
            if len(content.get('items', [])) < page_size:
                return None
            return {'offset': content.get('offset', 0) + page_size}

        return None
