# CloudPrompt MCP Server Documentation

## Overview

The CloudPrompt remote MCP (Model Context Protocol) Server is a comprehensive tool suite that provides AI agents with secure access to cloud infrastructure management capabilities across multiple providers. The server implements a session-based authentication system to ensure secure access to cloud resources.

## Supported Cloud Providers

- **AWS (Amazon Web Services)** - Full implementation with EC2, S3, and authentication tools
- **Proxmox** - Virtual machine management capabilities
- **Azure** - Placeholder implementation (development)
- **GCP (Google Cloud Platform)** - Placeholder implementation (development)

## ⚠️ Important Warnings

- **Apply principle of least privilege** to all credentials
- **All actions are final** - no undo functionality exists
- **Test thoroughly** before using in production environments

## Authentication

### AWS Authentication

AWS tools require session-based authentication. Call `authenticate_aws` first before using other AWS tools.

### Proxmox Authentication

Proxmox tools accept credentials as parameters or read from environment variables:
- `PROXMOX_HOST`, `PROXMOX_USER`, `PROXMOX_PASS`


### In development
User's Keycloak ID is sent along with requests, the MCP server queries the database for encrypted credentials and the MCP server decrypts them to generate a session ID to use for subsequent tool calls.

## AWS Tools

### Authentication Tools

| Tool Name | Description | Parameters | Return Type |
|-----------|-------------|------------|-------------|
| `authenticate_aws` | Authenticate with AWS and create a session (required first) | `region_name: str = "us-east-1"`<br>`aws_access_key_id: str = None`<br>`aws_secret_access_key: str = None` | `Dict` with session_id, account info, and auth status |

### EC2 (Elastic Compute Cloud) Tools

| Tool Name | Description | Parameters | Return Type |
|-----------|-------------|------------|-------------|
| `get_amis` | Get list of available AMIs for creating instances | `session_id: str` | `Dict` with region, total count, and AMI list |
| `create_ec2_instance` | Create new EC2 instance(s) | `MinCount: int`<br>`MaxCount: int`<br>`InstanceType: str`<br>`ImageId: str`<br>`session_id: str`<br>`StorageSize: int = 8`<br>`VolumeType: str = "gp3"`<br>`name: str = "CloudPrompt-Instance"`<br>`KeyName: str = None` | `Dict` with created instance information |
| `list_ec2_instances` | List all EC2 instances in region | `session_id: str` | `Dict` with instance list and details |
| `list_ec2_instance` | Get details of specific EC2 instance | `instance_id: str`<br>`session_id: str` | `Dict` with instance details |
| `start_ec2_instance` | Start a stopped EC2 instance | `instance_id: str`<br>`session_id: str` | `Dict` with operation status |
| `stop_ec2_instance` | Stop a running EC2 instance | `instance_id: str`<br>`session_id: str` | `Dict` with operation status |
| `terminate_ec2_instance` | Permanently delete EC2 instance | `instance_id: str`<br>`session_id: str` | `Dict` with operation status |
| `create_ssh_key_pair` | Create SSH key pair for EC2 access | `key_name: str`<br>`session_id: str`<br>`key_type: str = "rsa"` | `Dict` with key information and private key |
| `list_ssh_key_pairs` | List all SSH key pairs in region | `session_id: str` | `Dict` with key pair list |
| `delete_ssh_key_pair` | Delete SSH key pair | `key_name: str`<br>`session_id: str` | `Dict` with operation status |

### S3 (Simple Storage Service) Tools

| Tool Name | Description | Parameters | Return Type |
|-----------|-------------|------------|-------------|
| `create_s3_bucket` | Create new S3 bucket | `bucket_name: str`<br>`session_id: str` | `Dict` with bucket information |
| `list_s3_buckets` | List all S3 buckets | `session_id: str`<br>`check_empty: bool = False` | `Dict` with bucket list and metadata |
| `list_s3_bucket_objects` | List objects in specific S3 bucket | `bucket_name: str`<br>`session_id: str` | `Dict` with object list and details |
| `delete_s3_bucket_object` | Delete object from S3 bucket | `bucket_name: str`<br>`object_key: str`<br>`session_id: str` | `Dict` with operation status |
| `delete_s3_bucket` | Delete S3 bucket | `bucket_name: str`<br>`session_id: str`<br>`force: bool = False` | `Dict` with operation status |

## Proxmox Tools

| Tool Name | Description | Parameters | Return Type |
|-----------|-------------|------------|-------------|
| `list_vms` | List virtual machines on Proxmox node(s) | `node_name: str`<br>`proxmox_host: str = None`<br>`proxmox_user: str = None`<br>`proxmox_pass: str = None` | `List[Dict]` with VM details |

## Azure & GCP Tools (Development)

### Azure Tools
| Tool Name | Description | Parameters | Return Type |
|-----------|-------------|------------|-------------|
| `hello_azure` | Simple greeting tool for testing | `name: str` | `str` greeting message |

### GCP Tools  
| Tool Name | Description | Parameters | Return Type |
|-----------|-------------|------------|-------------|
| `hello_gcp` | Simple greeting tool for testing | `name: str` | `str` greeting message |
| `list_gcp_vms` | Placeholder VM listing tool | None | `list` of placeholder VMs |

**Remember: Apply principle of least privilege to credentials and test thoroughly before production use.**