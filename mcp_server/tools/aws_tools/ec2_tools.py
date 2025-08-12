import boto3
from botocore.exceptions import ClientError
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

def register_tools(mcp):

    @mcp.tool()
    async def get_ami_by_os(
        os_name: str,
        region_name: str = "us-east-1",
    ):
        '''
        Get AMI by OS name in a specific region.
        :param os_name: str - Name of the operating system (e.g., "Ubuntu Server 24.04 LTS").
        :param region_name: str -  AWS region name (default is "us-east-1").
        :return: Dict[str, Dict[str, str]] - List of AMIs for the specified OS in the given region.
        '''
        region_data = AMIs.get(region_name)
        if region_data:
            os_options = region_data.get("os_options", {})
            if os_name.lower() in os_options:
                logger.info(f"Found AMIs for OS '{os_name}' in region {region_name}")
                logger.info(f"AMIs list: {os_options[os_name.lower()]}")
                return {"AMIs": os_options[os_name.lower()]}

    @mcp.tool()
    async def get_default_ami(region_name: str = "us-east-1"):
        '''
        Get the default AMI for a specific region.
        :param region_name: str - AWS region name (default is "us-east-1").
        :return: Dict[str, str] - AMI ID for the specified region.   
        '''
        region_data = AMIs.get(region_name)
        if region_data:
            AMI = region_data["default"]
            logger.info(f"Fetching default AMI for region {region_name}: {AMI}")
            return {"AMI": AMI}
        return "Not found"

    @mcp.tool()
    async def create_ec2_instance(
        MinCount: int,
        MaxCount: int,
        InstanceType: str,
        ImageId: str,
        StorageSize: int = 8,
        VolumeType: str = "gp3",
        region_name: str = "us-east-1"
    ):
        '''
        Create an EC2 instance with specified parameters.
        :param MinCount: int - Minimum number of instances to launch.
        :param MaxCount: int -Maximum number of instances to launch.
        :param InstanceType: str - Type of instance to launch (e.g., "t2.micro").
        :param ImageId: str - ID of the AMI to use for the instance.
        :param StorageSize: int - Size of the root volume in GB (default is 8).
        :param VolumeType: str - Type of volume to create (default is "gp3").
        :param region_name: str -  AWS region name (default is "us-east-1").
        :return:  Dict[str, List[Dict[str, str]]] - Information about the created instances.
        '''
        logger.info(f"Creating EC2 instance: MinCount={MinCount}, MaxCount={MaxCount}, InstanceType={InstanceType}, ImageId={ImageId}, StorageSize={StorageSize}, VolumeType={VolumeType}, region={region_name}")
        try:
            ec2 = boto3.resource('ec2', region_name=region_name)
            instances = ec2.create_instances(
                ImageId=ImageId,
                MinCount=MinCount,
                MaxCount=MaxCount,
                InstanceType=InstanceType,
                BlockDeviceMappings=[
                    {
                        'DeviceName': '/dev/sda1',
                        'Ebs': {
                            'VolumeSize': StorageSize,
                            'DeleteOnTermination': True,
                            'VolumeType': VolumeType
                        }
                    }
                ]
            )
        except ClientError as e:
            logger.error(f"Error creating EC2 instance: {e}")
            return {"error": str(e)}

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
        '''
        Stop an EC2 instance by its ID.
        :param instance_id: str - ID of the EC2 instance to stop.
        :param region_name: str - AWS region name (default is "us-east-1").
        :return: Dict[str, str] - Information about the stopped instance.
        '''
        logger.info(f"Stopping EC2 instance: {instance_id} in region {region_name}")
        try:
            ec2 = boto3.resource('ec2', region_name=region_name)
            instance = ec2.Instance(instance_id)
            instance.stop()
        except ClientError as e:
            logger.error(f"Error stopping EC2 instance: {e}")
            return {"error": str(e)}
            
        logger.info(f"Stopped EC2 instance: {instance_id}")
        return {"stopped_instance_id": instance_id}

    @mcp.tool()
    async def list_ec2_instances(
        region_name: str = "us-east-1"
    ):
        '''
        List all EC2 instances in a specific region.
        :param region_name: str - AWS region name (default is "us-east-1").
        :return: Dict[str, List[Dict[str, str]]] - List of all EC2 instances in the specified region. 
        '''
        logger.info(f"Listing all EC2 instances in region {region_name}")
        try:
            ec2 = boto3.client('ec2', region_name=region_name)
            response = ec2.describe_instances()
        except ClientError as e:
            logger.error(f"Error listing EC2 instances: {e}")
            return {"error": str(e)}

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
        '''
        Get details of a specific EC2 instance by its ID.
        :param instance_id: str - ID of the EC2 instance to retrieve details for.
        :param region_name: str - AWS region name (default is "us-east-1").
        :return: Dict[str, List[Dict[str, str]]] - Details of the specified EC2 instance.
        '''
        logger.info(f"Getting details for EC2 instance: {instance_id} in region {region_name}")
        try:
            ec2 = boto3.client('ec2', region_name=region_name)
            response = ec2.describe_instances(InstanceIds=[instance_id])
        except ClientError as e:
            logger.error(f"Error getting details for EC2 instance {instance_id}: {e}")
            return {"error": str(e)}

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
        return {"instance": instances}

    @mcp.tool()
    async def start_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1"
    ):
        '''
        Start an EC2 instance by its ID.
        :param instance_id: str - ID of the EC2 instance to start.
        :param region_name: str - AWS region name (default is "us-east-1").
        :return: Dict[str, str] - Information about the started instance.
        '''
        logger.info(f"Starting EC2 instance: {instance_id} in region {region_name}")
        try:
            ec2 = boto3.resource('ec2', region_name=region_name)
            instance = ec2.Instance(instance_id)
            instance.start()
        except ClientError as e:
            logger.error(f"Error starting EC2 instance: {e}")
            return {"error": str(e)}

        logger.info(f"Started EC2 instance: {instance_id}")
        return {"started_instance_id": instance_id}

    @mcp.tool()
    async def terminate_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1"
    ):
        '''
        Terminate an EC2 instance by its ID.
        :param instance_id: str -  ID of the EC2 instance to terminate.
        :param region_name: str - AWS region name (default is "us-east-1").
        :return: Dict[str, str] Information about the terminated instance.
        '''
        logger.info(f"Terminating EC2 instance: {instance_id} in region {region_name}")
        try:
            ec2 = boto3.resource('ec2', region_name=region_name)
            instance = ec2.Instance(instance_id)
            instance.terminate()
        except ClientError as e:
            logger.error(f"Error terminating EC2 instance: {e}")
            return {"error": str(e)}

        logger.info(f"Terminated EC2 instance: {instance_id}")
        return {"terminated_instance_id": instance_id}