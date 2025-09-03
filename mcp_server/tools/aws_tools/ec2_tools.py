import boto3
from botocore.exceptions import ClientError
import logging

OFFICIAL_OWNERS = {
    "Amazon Linux": ["amazon"],            # alias supported
    "Ubuntu":       ["099720109477"],      # Canonical
    "Debian":       ["136693071363"],      # Debian
    "Red Hat":      ["309956199498"],      # Red Hat
    "SUSE Linux":   ["013907871322"],      # SUSE
}

NAME_PATTERNS = {
    "Amazon Linux": [
        "amzn2-ami-hvm-*-x86_64-*",
        "AL2023-AMI-*-x86_64",
        "al2023-ami-*-x86_64",
    ],
    "Ubuntu": [
        "ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*",
        "ubuntu/images/hvm-ssd-gp3/ubuntu-*-amd64-server-*",
    ],
    "Debian": [
        "debian-*-amd64-*",
    ],
    "Red Hat": [
        "RHEL-*-x86_64-*",
    ],
    "SUSE Linux": [
        "suse-sles-12-sp*-x86_64*",
        "suse-sles-15-sp*-x86_64*",
    ],
}

ordered_distros = ["Amazon Linux", "Ubuntu", "Debian", "Red Hat", "SUSE Linux"]

logger = logging.getLogger("aws_ec2_tools_mcp")

def register_tools(mcp):

    @mcp.tool()
    async def get_amis(
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        Get list of AMIs to create EC2 instances from.
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict with region, total, and list of AMIs.
        '''
        max_total = 15
        logger.info(f"Fetching Linux free-tier-friendly AMIs for region {region_name} (max_total={max_total})")
        try:
            # Create EC2 client with optional credentials
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                ec2 = boto3.client('ec2', region_name=region_name)

            quota = max(1, max_total // len(ordered_distros))

            def fetch_for_distro(distro: str) -> list[dict]:
                owners = OFFICIAL_OWNERS.get(distro, [])
                name_patterns = NAME_PATTERNS.get(distro, [])
                if not owners or not name_patterns:
                    return []

                # Query official owners with broad, future-proof name patterns
                resp = ec2.describe_images(
                    Owners=owners,
                    Filters=[
                        {"Name": "state", "Values": ["available"]},
                        {"Name": "name", "Values": name_patterns},
                        {"Name": "architecture", "Values": ["x86_64"]},
                        {"Name": "virtualization-type", "Values": ["hvm"]},
                        {"Name": "root-device-type", "Values": ["ebs"]},
                    ],
                )
                images = resp.get('Images', [])
                images.sort(key=lambda i: i.get('CreationDate', ''), reverse=True)

                out = []
                seen = set()
                for img in images:
                    iid = img.get('ImageId')
                    if not iid or iid in seen:
                        continue
                    seen.add(iid)
                    min_root_gb = None
                    for bdm in img.get('BlockDeviceMappings', []) or []:
                        if bdm.get('DeviceName'):
                            # VolumeSize represents the snapshot size and default root volume size (minimum)
                            min_root_gb = bdm['Ebs'].get('VolumeSize')
                            break
                    out.append({
                        'distribution': distro,
                        'ami_id': iid,
                        'description': img.get('Description', ''),
                        'mininimum_storage_size': min_root_gb,
                    })
                return out

            # Fetch per distro once
            fetched = {d: fetch_for_distro(d) for d in ordered_distros}

            # First pass: take up to quota from each distro
            result: list[dict] = []
            idx = {d: 0 for d in ordered_distros}
            for d in ordered_distros:
                taken = 0
                while taken < quota and idx[d] < len(fetched[d]) and len(result) < max_total:
                    result.append(fetched[d][idx[d]])
                    idx[d] += 1
                    taken += 1

            # Second pass: fill remaining slots from any distro
            while len(result) < max_total:
                progressed = False
                for d in ordered_distros:
                    if idx[d] < len(fetched[d]) and len(result) < max_total:
                        result.append(fetched[d][idx[d]])
                        idx[d] += 1
                        progressed = True
                if not progressed:
                    break

            logger.info(f"Returning {len(result)} AMIs for region {region_name}")
            return {
                'region': region_name,
                'total': len(result),
                'amis': result
            }

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Error fetching AMIs: {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            logger.error(f"Unexpected error fetching AMIs: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def create_ec2_instance(
        MinCount: int,
        MaxCount: int,
        InstanceType: str,
        ImageId: str,
        region_name: str = "us-east-1",
        StorageSize: int = 8,
        VolumeType: str = "gp3",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        name: str = None
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
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :param name: str - Optional name tag for the instance.
        :return:  Dict[str, List[Dict[str, str]]] - Information about the created instances.
        '''
        logger.info(f"Creating EC2 instance: MinCount={MinCount}, MaxCount={MaxCount}, InstanceType={InstanceType}, ImageId={ImageId}, StorageSize={StorageSize}, VolumeType={VolumeType}, region={region_name}")
        try:
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                ec2 = boto3.client('ec2', region_name=region_name)

            # Get minimum required root volume size from the AMI
            try:
                image_response = ec2.describe_images(ImageIds=[ImageId])
                min_root_size = 8  # Default minimum
                if image_response['Images']:
                    image = image_response['Images'][0]
                    for bdm in image.get('BlockDeviceMappings', []):
                        if bdm.get('DeviceName') == '/dev/sda1' and 'Ebs' in bdm:
                            min_root_size = bdm['Ebs'].get('VolumeSize', min_root_size)
                            break
                if StorageSize < min_root_size:
                    logger.warning(f"Requested StorageSize {StorageSize}GB is less than AMI minimum {min_root_size}GB. Adjusting to minimum.")
                    StorageSize = min_root_size
            except Exception as e:
                logger.warning(f"Could not determine AMI minimum root volume size: {e}. Proceeding with requested StorageSize {StorageSize}GB.")

            response = ec2.run_instances(
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
                ],
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [{'Key': 'Name', 'Value': name}] if name else []
                    }
                ]
            )
        except ClientError as e:
            logger.error(f"Error creating EC2 instance: {e}")
            return {"error": str(e)}

        instance_info = []
        for instance in response['Instances']:
            instance_info.append({
                "InstanceId": instance['InstanceId'],
                "Region": region_name
            })
            logger.info(f"Created EC2 instance: {instance['InstanceId']} in region {region_name}")
        return {"instances": instance_info}

    @mcp.tool()
    async def stop_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        Stop an EC2 instance by its ID.
        :param instance_id: str - ID of the EC2 instance to stop.
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict[str, str] - Information about the stopped instance.
        '''
        logger.info(f"Stopping EC2 instance: {instance_id} in region {region_name}")
        try:
            # Create boto3 client with provided credentials or fall back to environment/default
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2', 
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                ec2 = boto3.client('ec2', region_name=region_name)
                
            response = ec2.stop_instances(InstanceIds=[instance_id])
        except ClientError as e:
            logger.error(f"Error stopping EC2 instance: {e}")
            return {"error": str(e)}
            
        logger.info(f"Stopped EC2 instance: {instance_id}")
        return {"stopped_instance_id": instance_id}

    @mcp.tool()
    async def list_ec2_instances(
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        List all EC2 instances in a specific region.
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict[str, List[Dict[str, str]]] - List of all EC2 instances in the specified region. 
        '''
        logger.info(f"Listing all EC2 instances in region {region_name}")
        try:
            # Create boto3 client with provided credentials or fall back to environment/default
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2', 
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # Fall back to environment variables or default credential chain
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
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        Get details of a specific EC2 instance by its ID.
        :param instance_id: str - ID of the EC2 instance to retrieve details for.
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict[str, List[Dict[str, str]]] - Details of the specified EC2 instance.
        '''
        logger.info(f"Getting details for EC2 instance: {instance_id} in region {region_name}")
        try:
            # Create boto3 client with provided credentials or fall back to environment/default
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2', 
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
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
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        Start an EC2 instance by its ID.
        :param instance_id: str - ID of the EC2 instance to start.
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict[str, str] - Information about the started instance.
        '''
        logger.info(f"Starting EC2 instance: {instance_id} in region {region_name}")
        try:
            # Create boto3 client with provided credentials or fall back to environment/default
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2', 
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                ec2 = boto3.client('ec2', region_name=region_name)
                
            response = ec2.start_instances(InstanceIds=[instance_id])
        except ClientError as e:
            logger.error(f"Error starting EC2 instance: {e}")
            return {"error": str(e)}

        logger.info(f"Started EC2 instance: {instance_id}")
        return {"started_instance_id": instance_id}

    @mcp.tool()
    async def terminate_ec2_instance(
        instance_id: str,
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        Terminate an EC2 instance by its ID.
        :param instance_id: str -  ID of the EC2 instance to terminate.
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict[str, str] Information about the terminated instance.
        '''
        logger.info(f"Terminating EC2 instance: {instance_id} in region {region_name}")
        try:
            # Create boto3 client with provided credentials or fall back to environment/default
            if aws_access_key_id and aws_secret_access_key:
                ec2 = boto3.client(
                    'ec2', 
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                ec2 = boto3.client('ec2', region_name=region_name)
                
            response = ec2.terminate_instances(InstanceIds=[instance_id])
        except ClientError as e:
            logger.error(f"Error terminating EC2 instance: {e}")
            return {"error": str(e)}

        logger.info(f"Terminated EC2 instance: {instance_id}")
        return {"terminated_instance_id": instance_id}