import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
import uuid

logger = logging.getLogger("aws_auth_tools_mcp")

# Simple session storage: {session_id: session_data}
_sessions = {}

def register_tools(mcp):

    @mcp.tool()
    async def authenticate_aws(
        region_name: str = "us-east-1",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        '''
        Authenticate with AWS and create a session for subsequent operations.
        This tool MUST be called before any other AWS tools.
        
        :param region_name: str - AWS region name (default is "us-east-1").
        :param aws_access_key_id: str - AWS Access Key ID (optional, uses environment if not provided).
        :param aws_secret_access_key: str - AWS Secret Access Key (optional, uses environment if not provided).
        :return: Dict with authentication status, account info, and session_id.
        '''
        # Generate random session UUID
        session_id = str(uuid.uuid4())
        
        logger.info(f"Authenticating AWS session '{session_id}' for region {region_name}")
        
        try:
            # Create session with provided credentials or fall back to environment/default
            if aws_access_key_id and aws_secret_access_key:
                session = boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name
                )
            else:
                session = boto3.Session(region_name=region_name)
            
            # Test credentials by getting caller identity
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            
            # Store session for future use
            _sessions[session_id] = {
                'session': session,
                'region': region_name,
                'account_id': identity['Account'],
                'user_arn': identity['Arn'],
                'authenticated': True
            }
            
            logger.info(f"Successfully authenticated AWS session '{session_id}' for account {identity['Account']}")
            
            return {
                "status": "authenticated",
                "session_id": session_id,
                "account_id": identity['Account'],
                "user_arn": identity['Arn'],
                "region": region_name,
                "message": f"AWS session '{session_id}' authenticated successfully"
            }
            
        except NoCredentialsError:
            logger.error("No AWS credentials found")
            return {
                "status": "error",
                "message": "No AWS credentials found. Please provide aws_access_key_id and aws_secret_access_key or configure AWS credentials."
            }
        except ClientError as e:
            error_msg = str(e)
            logger.error(f"AWS authentication failed: {error_msg}")
            return {
                "status": "error",
                "message": f"Authentication failed: {error_msg}"
            }
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

def get_aws_client(service_name: str, session_id: str):
    '''
    Helper function to get a boto3 client for a specific service from an authenticated session.
    
    :param service_name: str - AWS service name (e.g., 'ec2', 's3', 'sts').
    :param session_id: str - Session identifier from authenticate_aws.
    :return: boto3 client instance or None if session not found.
    '''
    if session_id not in _sessions:
        logger.error(f"Session '{session_id}' not found. Please authenticate first.")
        return None
    
    session_info = _sessions[session_id]
    if not session_info['authenticated']:
        logger.error(f"Session '{session_id}' is not authenticated.")
        return None
    
    try:
        client = session_info['session'].client(service_name)
        logger.debug(f"Created {service_name} client for session '{session_id}'")
        return client
    except Exception as e:
        logger.error(f"Failed to create {service_name} client: {e}")
        return None

def get_aws_session_region(session_id: str):
    '''
    Helper function to get the region for a specific session.
    
    :param session_id: str - Session identifier from authenticate_aws.
    :return: str - Region name or None if session not found.
    '''
    if session_id not in _sessions:
        return None
    return _sessions[session_id]['region']
