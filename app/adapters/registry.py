from typing import Literal

AuthType = Literal["none", "bearer", "api_key", "aws_sigv4"]

SUPPORTED_ADAPTERS = {"github", "randomuser", "aws", "mock", "jsonplaceholder", "coingecko"}
