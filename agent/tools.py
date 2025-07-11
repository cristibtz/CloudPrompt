from agents import function_tool
import boto3

@function_tool
def create_ec2_vm(
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
def stop_ec2_vm(
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
