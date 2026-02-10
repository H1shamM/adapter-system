from typing import Dict, List
import boto3

from app.adapters.base import BaseAdapter, AdapterConfig

class AWSConfig(AdapterConfig):
    """AWS-specific configuration"""
    resource_types: list = ["ec2"]
    auth_config: Dict[str, str] = {
        "access_key": "",
        "secret_key": "",
        "region": "us-east-1"
    }


class AWSAdapter(BaseAdapter):
    HTTP_CONFIG_CLASS = AWSConfig

    def __init__(self, config: AWSConfig):
        super().__init__(config)
        self.session = boto3.Session(
            aws_access_key_id=config.access_key.get_secret_value(),
            aws_secret_access_key=config.secret_key.get_secret_value(),
            region_name=config.region
        )

    def connect(self) -> bool:
        sts = self.session.client('sts')
        try:
            sts.get_caller_identity()
            return True
        except Exception:
            return False

    def fetch_raw(self) -> List[Dict]:
        ec2 = self.session.resource('ec2')
        return [instance.meta.data for instance in ec2.instances.all()]

    def normalize(self, raw_data: List[Dict]) -> List[Dict]:
        return [{
            "asset_id": f"aws_ec2_{instance['InstanceId']}",
            "name": next(
                (tag['Value'] for tag in instance.get('Tags', [])
                 if tag['Key'] == 'Name'),
                "Unnamed Instance"
            ),
            "type": "ec2",
            "status": instance["State"]["Name"].upper(),
            "created_at": instance["LaunchTime"].isoformat(),
            "metadata": {
                "instance_type": instance["InstanceType"],
                "public_ip": instance.get("PublicIpAddress"),
                "vpc_id": instance["VpcId"]
            }
        } for instance in raw_data]
