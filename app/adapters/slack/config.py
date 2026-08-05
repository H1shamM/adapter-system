from typing import List

from pydantic import Field

from app.adapters.base import AdapterConfig


class SlackConfig(AdapterConfig):
    """Slack Web API configuration. Auth is a plain bearer bot token (VAR:SLACK_BOT_TOKEN via
    auth_config, same as GitHub's bearer setup) -- no new auth strategy needed."""

    channel_types: List[str] = Field(
        default_factory=lambda: ["public_channel"],
        description="Passed to conversations.list 'types' param",
    )
    message_history_limit: int = Field(
        default=200, description="Max messages fetched per channel across pagination"
    )
