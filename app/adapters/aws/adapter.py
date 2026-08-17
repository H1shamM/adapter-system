import asyncio
from datetime import datetime
from typing import AsyncIterator, Dict, List

import boto3

from app.adapters.base import AdapterConfig, BaseAdapter
from app.adapters.errors import AuthenticationError, FetchError
from app.config import settings
from app.models.assets import NormalizedAsset


class AWSConfig(AdapterConfig):
    """AWS-specific configuration"""

    resource_types: list = ["ec2"]
    auth_config: Dict[str, str] = {"access_key": "", "secret_key": "", "region": "us-east-1"}


class AWSAdapter(BaseAdapter):
    HTTP_CONFIG_CLASS = AWSConfig

    def __init__(self, config: AWSConfig):
        super().__init__(config)
        self.session = boto3.Session(
            aws_access_key_id=config.auth_config.get("access_key"),
            aws_secret_access_key=config.auth_config.get("secret_key"),
            region_name=config.auth_config.get("region", "us-east-1"),
        )

    async def connect(self) -> None:
        sts = self.session.client("sts")
        try:
            await asyncio.to_thread(sts.get_caller_identity)
        except Exception as exc:
            raise AuthenticationError(f"AWS STS get_caller_identity failed: {exc}") from exc

    async def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """boto3's EC2 resource collection already paginates internally (~1000 instances/page) --
        bridge it one page at a time via asyncio.to_thread(next, ...) instead of forcing the whole
        collection into one list first, so a huge fleet doesn't have to be fully materialized
        before storage sees anything."""
        try:
            ec2 = self.session.resource("ec2")
            pages = ec2.instances.pages()  # sync generator -- no I/O until the first next()
            while True:
                page = await asyncio.to_thread(next, pages, None)
                if page is None:
                    break
                yield [instance.meta.data for instance in page]
        except Exception as exc:
            raise FetchError(f"AWS EC2 fetch failed: {exc}") from exc

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        return [
            NormalizedAsset(
                asset_id=f"aws_ec2_{instance['InstanceId']}",
                customer_id=settings.customer_id,
                name=next(
                    (tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"),
                    "Unnamed Instance",
                ),
                asset_type="ec2",
                status=instance["State"]["Name"].upper(),
                last_seen=(
                    instance["LaunchTime"]
                    if isinstance(instance["LaunchTime"], datetime)
                    else datetime.fromisoformat(instance["LaunchTime"])
                ),
                vendor="AWS",
                metadata={
                    "instance_type": instance["InstanceType"],
                    "public_ip": instance.get("PublicIpAddress"),
                    "vpc_id": instance["VpcId"],
                },
            )
            for instance in raw_data
        ]
