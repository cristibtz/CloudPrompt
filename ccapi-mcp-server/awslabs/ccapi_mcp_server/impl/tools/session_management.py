# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Session management implementation for CCAPI MCP server.

This version enforces explicit AWS credentials passed in by the caller. No
environment/profile fallback is allowed for new workflows.
"""

import datetime
import uuid
from awslabs.ccapi_mcp_server.aws_client import get_aws_client_with_credentials
from awslabs.ccapi_mcp_server.context import Context
from awslabs.ccapi_mcp_server.errors import ClientError
from os import environ


def check_aws_credentials(
    aws_access_key_id: str | None,
    aws_secret_access_key: str | None,
    aws_session_token: str | None,
    region: str | None,
) -> dict:
    """Validate explicit AWS credentials by calling STS GetCallerIdentity.

    Returns a dict with validity and identity info. Does not fall back to env/profile.
    """
    if not aws_access_key_id or not aws_secret_access_key:
        return {
            'valid': False,
            'error': 'Missing AWS credentials: aws_access_key_id and aws_secret_access_key are required',
            'region': region or 'us-east-1',
            'credential_source': 'explicit',
        }

    try:
        sts_client = get_aws_client_with_credentials(
            'sts', region or 'us-east-1', aws_access_key_id, aws_secret_access_key, aws_session_token
        )
        identity = sts_client.get_caller_identity()
        return {
            'valid': True,
            'account_id': identity.get('Account', 'Unknown'),
            'arn': identity.get('Arn', 'Unknown'),
            'user_id': identity.get('UserId', 'Unknown'),
            'region': region or 'us-east-1',
            'credential_source': 'explicit',
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'region': region or 'us-east-1',
            'credential_source': 'explicit',
        }


async def check_environment_variables_impl(
    workflow_store: dict,
    *,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_session_token: str | None = None,
    region: str | None = None,
) -> dict:
    """Validate provided AWS credentials and produce an environment token.

    This function does NOT read environment variables or profiles.
    """
    cred_check = check_aws_credentials(
        aws_access_key_id, aws_secret_access_key, aws_session_token, region
    )

    # Generate environment token
    environment_token = f'env_{str(uuid.uuid4())}'

    # Store environment validation results
    workflow_store[environment_token] = {
        'type': 'environment',
        'data': {
            'environment_variables': {},
            'aws_profile': '',
            'aws_region': cred_check.get('region') or 'us-east-1',
            'properly_configured': cred_check.get('valid', False),
            'readonly_mode': Context.readonly_mode(),
            'aws_auth_type': 'explicit',
            'needs_profile': False,
            'error': cred_check.get('error'),
            # Store raw credentials for next step
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'aws_session_token': aws_session_token,
        },
        'parent_token': None,  # Root token
        'timestamp': datetime.datetime.now().isoformat(),
    }

    env_data = workflow_store[environment_token]['data']

    return {
        'environment_token': environment_token,
        'message': 'Environment validation completed. Use this token with get_aws_session_info().',
        **env_data,  # Include environment data for display
    }


async def get_aws_session_info_impl(environment_token: str, workflow_store: dict) -> dict:
    """Get information about the current AWS session implementation.

    IMPORTANT: Always display the AWS context information to the user when this tool is called.
    Show them: AWS Profile (or "Environment Variables"), Authentication Type, Account ID, and Region so they know
    exactly which AWS account and region will be affected by any operations.
    """
    # Validate environment token
    if environment_token not in workflow_store:
        raise ClientError(
            'Invalid environment token: you must call check_environment_variables() first'
        )

    env_data = workflow_store[environment_token]['data']
    if not env_data.get('properly_configured', False):
        error_msg = env_data.get('error', 'Environment is not properly configured.')
        raise ClientError(error_msg)

    # Validate previously provided credentials
    cred_check = check_aws_credentials(
        env_data.get('aws_access_key_id'),
        env_data.get('aws_secret_access_key'),
        env_data.get('aws_session_token'),
        env_data.get('aws_region'),
    )

    if not cred_check.get('valid', False):
        raise ClientError(f'AWS credentials are not valid: {cred_check.get("error", "Unknown error")}')

    # Generate credentials token
    credentials_token = f'creds_{str(uuid.uuid4())}'

    # Build session info with credential masking
    arn = cred_check.get('arn', 'Unknown')
    user_id = cred_check.get('user_id', 'Unknown')

    session_data = {
    'profile': '',
        'account_id': cred_check.get('account_id', 'Unknown'),
        'region': cred_check.get('region') or 'us-east-1',
        'arn': f'{"*" * (len(arn) - 8)}{arn[-8:]}' if len(arn) > 8 and arn != 'Unknown' else arn,
        'user_id': f'{"*" * (len(user_id) - 4)}{user_id[-4:]}'
        if len(user_id) > 4 and user_id != 'Unknown'
        else user_id,
    'credential_source': 'explicit',
        'readonly_mode': Context.readonly_mode(),
        'readonly_message': (
            """⚠️ This server is running in READ-ONLY MODE. I can only list and view existing resources.
    I cannot create, update, or delete any AWS resources. I can still generate example code
    and run security checks on templates."""
            if Context.readonly_mode()
            else ''
        ),
    'credentials_valid': True,
    'aws_auth_type': 'explicit',
    # Store raw credentials for downstream tools
    'aws_access_key_id': env_data.get('aws_access_key_id'),
    'aws_secret_access_key': env_data.get('aws_secret_access_key'),
    'aws_session_token': env_data.get('aws_session_token'),
    }

    # Add masked environment variables if using env vars
    access_key = env_data.get('aws_access_key_id') or ''
    secret_key = env_data.get('aws_secret_access_key') or ''
    session_data['masked_credentials'] = {
        'AWS_ACCESS_KEY_ID': f'{"*" * (len(access_key) - 4)}{access_key[-4:]}'
        if len(access_key) > 4
        else '****',
        'AWS_SECRET_ACCESS_KEY': f'{"*" * (len(secret_key) - 4)}{secret_key[-4:]}'
        if len(secret_key) > 4
        else '****',
    }

    # Store session information
    workflow_store[credentials_token] = {
        'type': 'credentials',
        'data': session_data,
        'parent_token': environment_token,
        'timestamp': datetime.datetime.now().isoformat(),
    }

    return {
        'credentials_token': credentials_token,
        'message': 'AWS session validated. Use this token with generate_infrastructure_code().',
        'DISPLAY_TO_USER': 'YOU MUST SHOW THE USER THEIR AWS SESSION INFORMATION FOR SECURITY',
        **session_data,  # Include all session data for display
    }


def get_aws_profile_info():
    """Deprecated in explicit-credentials mode. Kept for startup logging."""
    return {
        'profile': '',
        'account_id': 'Unknown',
        'region': environ.get('AWS_REGION') or 'us-east-1',
        'arn': 'Unknown',
        'using_env_vars': False,
    }
