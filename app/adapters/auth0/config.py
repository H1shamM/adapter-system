from app.adapters.base import AdapterConfig


class Auth0Config(AdapterConfig):
    """Auth0-specific configuration.

    Auth itself is NOT a new field here -- it reuses the existing generic
    auth_type / auth_config mechanism inherited from HttpClientConfig, the
    same way every other adapter does (see GitHubConfig, AWSConfig).

    Expected instantiation:
        Auth0Config(
            name="auth0",
            domain="dev-xxxx.us.auth0.com",
            auth_type="oauth2_client_credentials",   # new strategy -- see app/http/client.py
            auth_config={
                "client_id": "VAR:AUTH0_CLIENT_ID",
                "client_secret": "VAR:AUTH0_CLIENT_SECRET",
                "audience": "https://dev-xxxx.us.auth0.com/api/v2/",
            },
        )
    """

    domain: str  # e.g. "dev-d1fkow8qwvxutvxp.us.auth0.com" -- used for both the
    # token URL (https://{domain}/oauth/token) and the Management API base_url
