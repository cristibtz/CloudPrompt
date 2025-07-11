from agents import function_tool
import boto3

@function_tool
def create_ec2_instance(
    MinCount: int,
    MaxCount: int,
    InstanceType: str,
    ImageId: str = "ami-020cba7c55df1f615",
    region_name: str = "us-east-1"
):
    """
    Create an EC2 instance with the given parameters.
    """
    ec2 = boto3.resource('ec2', region_name=region_name)
    instances = ec2.create_instances(
        ImageId=ImageId,
        MinCount=MinCount,
        MaxCount=MaxCount,
        InstanceType=InstanceType
    )
    return {"instance_ids": [i.id for i in instances]}

@function_tool
def stop_ec2_instance(
    instance_id: str,
    region_name: str = "us-east-1"
):
    """
    Stop an EC2 instance by instance ID.
    """
    ec2 = boto3.resource('ec2', region_name=region_name)
    instance = ec2.Instance(instance_id)
    instance.stop()
    return {"stopped_instance_id": instance_id}

@function_tool
def list_ec2_instances(
    region_name: str = "us-east-1"
):
    """
    List all EC2 instances in the specified region.
    """
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
    return {"instances": instances}

@function_tool
def list_ec2_instance(
    instance_id: str,
    region_name: str = "us-east-1"
):
    """
    Get details of a specific EC2 instance by instance ID.
    """
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
    return {"instances": instances}

@function_tool
def start_ec2_instance(
    instance_id: str,
    region_name: str = "us-east-1"
):
    """
    Start an EC2 instance by instance ID.
    """
    ec2 = boto3.resource('ec2', region_name=region_name)
    instance = ec2.Instance(instance_id)
    instance.start()
    return {"started_instance_id": instance_id}