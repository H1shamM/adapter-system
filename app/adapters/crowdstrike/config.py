from typing import Optional

from app.adapters.base import AdapterConfig


class CrowdStrikeConfig(AdapterConfig):
    """CrowdStrike Falcon (Hosts + User Management APIs) configuration.

    Auth flows through the generic oauth2_client_credentials strategy, generalized (see
    app/http/client.py) to support CrowdStrike's shape: form-encoded token request, only
    client_id/client_secret (no grant_type/audience, unlike Auth0's JSON+grant_type+audience shape).

    Expected instantiation:
        CrowdStrikeConfig(
            name="crowdstrike",
            base_url="https://api.us-1.crowdstrike.com",  # region-specific -- see CrowdStrike docs
            auth_type="oauth2_client_credentials",
            auth_config={
                "client_id": "VAR:CROWDSTRIKE_CLIENT_ID",
                "client_secret": "VAR:CROWDSTRIKE_CLIENT_SECRET",
                "token_url": "/oauth2/token",  # relative -- same host as base_url
                "token_body_format": "form",
            },
        )
    """

    device_filter: Optional[str] = None  # optional FQL filter, e.g. "platform_name:'Windows'"

    # Per-user detail+roles enrichment (stream()) runs concurrently within each page, bounded by
    # this -- respects CrowdStrike's documented per-endpoint rate limits, configurable per tenant.
    max_concurrent_requests: int = 10
