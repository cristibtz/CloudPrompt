import logging
import asyncio
import httpx
import boto3
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aws_ec2_manager_mcp")

http_client = httpx.AsyncClient(timeout=10.0)

mcp = FastMCP("AWS EC2 Manager MCP Server")

@mcp.tool()
async def create_ec2_instance(
    MinCount: int,
    MaxCount: int,
    InstanceType: str,
    ImageId: str = "ami-020cba7c55df1f615",
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
    instance_ids = [i.id for i in instances]
    logger.info(f"Created EC2 instances: {instance_ids}")
    return {"instance_ids": instance_ids}

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

if __name__ == "__main__":
    try:
        logger.info("Starting MCP server on port 8000...")
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        asyncio.run(http_client.aclose())