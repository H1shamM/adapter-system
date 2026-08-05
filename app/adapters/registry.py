from typing import Literal

AuthType = Literal["none", "bearer", "api_key", "aws_sigv4", "oauth2_client_credentials"]

SUPPORTED_ADAPTERS = {
    "github",
    "randomuser",
    "aws",
    "mock",
    "jsonplaceholder",
    "coingecko",
    "perftest",
    "auth0",
    "slack",
    "crowdstrike",
}
