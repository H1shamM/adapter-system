from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)


class DatabaseSettings(BaseSettings):
    """Database settings"""

    mongo_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string"
    )

    mongo_db_name: str = Field(
        default="asset_management",
        description="Database name"
    )

    mongo_max_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max Connection in pool"
    )

    mongo_min_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Min Connection in pool"
    )

    model_config = SettingsConfigDict(
        env_prefix="MONGO_",
        case_sensitive=False
    )


class ClientSettings(BaseSettings):
    """Client settings"""

    default_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
    )

    default_max_retries: int = Field(
        default=3,
        ge=1,
        le=5,
    )

    default_retry_wait: int = Field(
        default=5,
        ge=1,
        le=60,
    )


class CelerySettings(BaseSettings):
    """Celery settings"""
    broker_url: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        description="Celery broker connection string"
    )

    result_backend: str = Field(
        default="rpc://",
        description="Result backend"
    )

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        case_sensitive=False
    )


class RedisSettings(BaseSettings):
    """Redis settings"""

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )

    redis_max_connections: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False
    )


class APISettings(BaseSettings):
    """API settings"""
    api_host: str = Field(
        default="0.0.0.0",
        description="API host"
    )

    api_port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
    )

    api_debug: bool = Field(
        default=False,
        description="Debug mode"
    )

    api_cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="CORS origins"
    )

    api_jwt_secret_key: SecretStr = Field(
        default=SecretStr("secret"),
        description="JWT secret key"
    )

    api_jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )

    api_jwt_expiration_minutes: int = Field(
        default=60,
        description="JWT expiration minutes"
    )

    api_jwt_refresh_token_expiration_days: int = Field(
        default=7,
        description="JWT refresh token expiration days"
    )

    api_rate_limit_enabled: bool = Field(
        default=True,
        description="Enable/disable rate limiting"
    )

    api_limit_per_minute: int = Field(
        default=100,
        description="Limit per minute"
    )

    model_config = SettingsConfigDict(
        env_prefix="API_",
        case_sensitive=False
    )


class LoggingSettings(BaseSettings):
    """Logging settings"""
    log_level: str = Field(
        default="INFO",
        description="Log level"
    )

    log_format: str = Field(
        default="json",
        description="Log format"
    )

    log_file: str = Field(
        default="/var/log/adapter-system.log",
        description="Log file"
    )

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False
    )


class Settings(BaseSettings):
    app_name: str = Field(default="AdapterSystem")
    app_version: str = Field(default="1.0.0")
    environment: Literal["production", "development"] = Field(default="development")

    customer_id: str = Field(
        default="default_customer_id",
        description="Unique customer identifier for this instance"
    )

    instance_id: str = Field(
        default="default_instance_id",
        description="Unique instance identifier (e.g., acme-prod-us-east-1)"
    )

    client: ClientSettings = Field(default_factory=ClientSettings)
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    pythonunbuffered: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


def is_production(self):
    """Production settings"""
    return self.environment.lower() == "production"


def is_development(self):
    """Development settings"""
    return self.environment.lower() == "development"


settings = Settings()


def get_settings():
    return settings
