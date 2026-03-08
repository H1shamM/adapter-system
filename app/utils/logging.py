"""
Structured logging with customer context.
All loggings automatically include customer id for centralized debugging
"""
import logging

import structlog

from app.config import settings


def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the customer context automatically bound.

    Usage:
        logger = get_logger(__name__)
        logger.info("sync_stated", adapter_type="github", assets=150)

    Output (Json):
        {
            "event": "sync_stated",
            "customer_id": "acme_corp",
            "instance_id": "acme-prod-us-east-1",
            "adapter_type": "github",
            "assets": 150,
            "timestamp": "2026-01-01T00:00:00Z",
        }
    """
    logger = structlog.get_logger(name)

    logger = logger.bind(
        customer_id=settings.customer_id,
        instance_id=settings.instance_id,
    )

    return logger
