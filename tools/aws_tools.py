import boto3
import logging

DEFAULT_AMIS = {
    "us-east-1": "ami-020cba7c55df1f615",
    "us-west-2": "ami-05f991c49d264708f"
}

logger = logging.getLogger("aws_ec2_manager_mcp")

def register_aws_tools(mcp):

    @mcp.tool()
    async def get_default_ami(region_name: str = "us-east-1"):
        return {
            "us-east-1": "ami-020cba7c55df1f615", 
            "us-west-2": "ami-05f991c49d264708f "
        }

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
                    'InstanceType': instance['InstanceType']
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
                    'InstanceType': instance['InstanceType']
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