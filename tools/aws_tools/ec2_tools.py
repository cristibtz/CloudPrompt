import boto3
import logging

AMIs = {
    "us-east-1": {
        "default": "ami-020cba7c55df1f615",
        "os_options": {
            "ubuntu": {
                "Ubuntu Server 24.04 LTS": "ami-020cba7c55df1f615",
                "Ubuntu Server 22.04 LTS": "ami-0a7d80731ae1b2435"
            }
        }
    },
    "us-east-2": {
        "default": "ami-0d1b5a8c13042c939",
        "os_options": {
            "ubuntu": {
                "Ubuntu Server 24.04 LTS": "ami-0d1b5a8c13042c939",
                "Ubuntu Server 22.04 LTS": "ami-0b05d988257befbbe"
            }
        }
    },
    "us-west-1": {
        "default": "ami-014e30c8a36252ae5",
        "os_options": {
            "ubuntu": {
                "Ubuntu Server 24.04 LTS": "ami-014e30c8a36252ae5",
                "Ubuntu Server 22.04 LTS": "ami-043b59f1d11f8f189"
            }
        }
    },
    "us-west-2": {
        "default": "ami-05f991c49d264708f",
        "os_options": {
            "ubuntu": {
                "Ubuntu Server 24.04 LTS": "ami-05f991c49d264708f",
                "Ubuntu Server 22.04 LTS": "ami-0987654321fedcba0"
            }
        }
    }
}


logger = logging.getLogger("aws_ec2_tools_mcp")

def register_aws_tools(mcp):

    @mcp.tool()
    async def get_ami_by_os(
        os_name: str,
        region_name: str = "us-east-1",
    ):
        region_data = AMIs.get(region_name)
        if region_data:
            os_options = region_data.get("os_options", {})
            if os_name.lower() in os_options:
                logger.info(f"Found AMIs for OS '{os_name}' in region {region_name}")
                logger.info(f"AMIs list: {os_options[os_name.lower()]}")
                return {"AMIs": os_options[os_name.lower()]}

    @mcp.tool()
    async def get_default_ami(region_name: str = "us-east-1"):
        region_data = AMIs.get(region_name)
        if region_data:
            AMI = region_data["default"]
            logger.info(f"Fetching default AMI for region {region_name}: {AMI}")
            return AMI
        return "Not found"

    @mcp.tool()
    async def create_ec2_instance(
        MinCount: int,
        MaxCount: int,
        InstanceType: str,
        ImageId: str,
        region_name: str = "us-east-1"
    ):
        logger.info(f"Creating EC2 instance: MinCount={MinCount}, MaxCount={MaxCount}, InstanceType={InstanceType}, ImageId={ImageId}, region={region_name}")
        ec2 = boto3.resource('ec2', region_name=region_name)
        instances = ec2.create_instances(
            ImageId=ImageId,
            MinCount=MinCount,
            MaxCount=MaxCount,
            InstanceType=InstanceType
        )
        instance_info = []
        for instance in instances:
            instance_info.append({
                "InstanceId": instance.id,
                "Region": region_name
            })
            logger.info(f"Created EC2 instance: {instance.id} in region {region_name}")
        return {"instances": instance_info}

    @mcp.tool()
    async def stop_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1"
    ):
        logger.info(f"Stopping EC2 instance: {instance_id} in region {region_name}")
        ec2 = boto3.resource('ec2', region_name=region_name)
        instance = ec2.Instance(instance_id)
        instance.stop()
        logger.info(f"Stopped EC2 instance: {instance_id}")
        return {"stopped_instance_id": instance_id}

    @mcp.tool()
    async def list_ec2_instances(
        region_name: str = "us-east-1"
    ):
        logger.info(f"Listing all EC2 instances in region {region_name}")
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'State': instance['State']['Name'],
                    'InstanceType': instance['InstanceType'],
                    'Public IPv4': instance.get('PublicIpAddress')
                })
        logger.info(f"Found {len(instances)} EC2 instances in region {region_name}")
        return {"instances": instances}

    @mcp.tool()
    async def list_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1"
    ):
        logger.info(f"Getting details for EC2 instance: {instance_id} in region {region_name}")
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'State': instance['State']['Name'],
                    'InstanceType': instance['InstanceType'],
                    'Public IPv4': instance.get('PublicIpAddress'), 
                })
        logger.info(f"Details for EC2 instance {instance_id}: {instances}")
        return {"instances": instances}

    @mcp.tool()
    async def start_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1"
    ):
        logger.info(f"Starting EC2 instance: {instance_id} in region {region_name}")
        ec2 = boto3.resource('ec2', region_name=region_name)
        instance = ec2.Instance(instance_id)
        instance.start()
        logger.info(f"Started EC2 instance: {instance_id}")
        return {"started_instance_id": instance_id}

    @mcp.tool()
    async def terminate_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1"
    ):
        logger.info(f"Terminating EC2 instance: {instance_id} in region {region_name}")
        ec2 = boto3.resource('ec2', region_name=region_name)
        instance = ec2.Instance(instance_id)
        instance.terminate()
        logger.info(f"Terminated EC2 instance: {instance_id}")
        return {"terminated_instance_id": instance_id}