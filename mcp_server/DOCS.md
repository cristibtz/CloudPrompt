# MCP Server tools documentation

## EC2 tools

| Tool Name | Description | Parameters | Return Type | Example Usage |
|-----------|-------------|------------|-------------|---------------|
| `get_ami_by_os` | Get AMI by OS name in a specific region | `os_name: str` - Name of the operating system (e.g., "ubuntu")<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, Dict[str, str]]` - Dictionary containing AMIs for the specified OS | `get_ami_by_os("ubuntu", "us-east-1")` |
| `get_default_ami` | Get the default AMI for a specific region | `region_name: str = "us-east-1"` - AWS region name | `Dict[str, str]` - Dictionary containing default AMI ID for the specified region | `get_default_ami("us-west-2")` |
| `create_ec2_instance` | Create an EC2 instance with specified parameters | `MinCount: int` - Minimum number of instances to launch<br>`MaxCount: int` - Maximum number of instances to launch<br>`InstanceType: str` - Type of instance (e.g., "t2.micro")<br>`ImageId: str` - ID of the AMI to use<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, List[Dict[str, str]]]` - Information about created instances | `create_ec2_instance(1, 1, "t2.micro", "ami-020cba7c55df1f615")` |
| `stop_ec2_instance` | Stop an EC2 instance by its ID | `instance_id: str` - ID of the EC2 instance to stop<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, str]` - Information about the stopped instance | `stop_ec2_instance("i-1234567890abcdef0")` |
| `list_ec2_instances` | List all EC2 instances in a specific region | `region_name: str = "us-east-1"` - AWS region name | `Dict[str, List[Dict[str, str]]]` - List of all EC2 instances in the region | `list_ec2_instances("us-west-1")` |
| `list_ec2_instance` | Get details of a specific EC2 instance by its ID | `instance_id: str` - ID of the EC2 instance to retrieve details for<br>`region_name: str = "us-east-1"` - AWS region name | ` Dict[str, List[Dict[str, str]]]` - Details of the specified EC2 instance | `list_ec2_instance("i-1234567890abcdef0")` |
| `start_ec2_instance` | Start an EC2 instance by its ID | `instance_id: str` - ID of the EC2 instance to start<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, str]` - Information about the started instance | `start_ec2_instance("i-1234567890abcdef0")` |
| `terminate_ec2_instance` | Terminate an EC2 instance by its ID | `instance_id: str` - ID of the EC2 instance to terminate<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, str]` - Information about the terminated instance | `terminate_ec2_instance("i-1234567890abcdef0")` |

## S3 tools

| Tool Name | Description | Parameters | Return Type | Example Usage |
|-----------|-------------|------------|-------------|---------------|
| `create_s3_bucket` | Create an S3 bucket in a specific region | `bucket_name: str` - Name of the S3 bucket to create<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, str]` - Information about the created bucket | `create_s3_bucket("my-bucket", "us-west-2")` |
| `list_s3_buckets` | List all S3 buckets | `region_name: str = "us-east-1"` - AWS region name (ignored, lists all buckets)<br>`check_empty: bool = False` - Whether to check if buckets are empty | `Dict[str, List[Dict[str, str]]]` - List of buckets with their metadata | `list_s3_buckets("us-east-1", True)` |
| `list_s3_bucket_objects` | List all objects in a specific S3 bucket | `bucket_name: str` - Name of the S3 bucket to list objects from<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, List[Dict[str, Union[str, int]]]]` - List of objects with their keys, sizes, and last modified dates | `list_s3_bucket_objects("my-bucket")` |
| `delete_s3_bucket` | Delete an S3 bucket with optional force empty | `bucket_name: str` - Name of the S3 bucket to delete<br>`force: bool = False` - Whether to force delete by emptying the bucket first<br>`region_name: str = "us-east-1"` - AWS region name | `Dict[str, str]` - Information about the deleted bucket or error message | `delete_s3_bucket("my-bucket", True)` |