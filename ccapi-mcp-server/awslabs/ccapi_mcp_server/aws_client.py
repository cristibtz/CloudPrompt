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

import botocore.config
from awslabs.ccapi_mcp_server import __version__
from awslabs.ccapi_mcp_server.errors import ClientError
from boto3 import Session
import boto3
from os import environ


session_config = botocore.config.Config(
    user_agent_extra=f'ccapi-mcp-server/{__version__}',
)


def get_aws_client(service_name, region_name=None):
    """Create and return an AWS service client using boto3's default credential chain.

    Args:
        service_name: AWS service name (e.g., 'cloudcontrol', 'logs', 'marketplace-catalog')
        region_name: AWS region name (defaults to boto3's default region resolution)

    Returns:
        Boto3 client for the specified service
    """
    # Handle FieldInfo objects (from pydantic)
    if hasattr(region_name, 'default') and region_name is not None:
        region_name = region_name.default

    # AWS Region Resolution Order (highest to lowest priority):
    # 1. region_name argument passed to this function
    # 2. AWS_REGION environment variable
    # 3. region setting in ~/.aws/config for the active profile
    # 4. "us-east-1" as the final fallback
    #
    # This follows boto3's standard region resolution chain, ensuring consistent
    # behavior with other AWS tools and SDKs.
    profile_name = environ.get('AWS_PROFILE')
    session = Session(profile_name=profile_name) if profile_name else Session()

    try:
        return session.client(service_name, region_name=region_name, config=session_config)
    except Exception as e:
        if 'ExpiredToken' in str(e):
            raise ClientError('Your AWS credentials have expired. Please refresh them.')
        elif 'NoCredentialProviders' in str(e):
            raise ClientError(
                'No AWS credentials found. Please configure credentials using environment variables or AWS configuration.'
            )
        else:
            raise ClientError('Got an error when loading your client.')


def get_aws_client_with_credentials(
    service_name: str,
    region_name: str | None,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_session_token: str | None = None,
):
    """Create and return an AWS service client using explicit credentials only.

    Args:
        service_name: AWS service name (e.g., 'cloudcontrol', 'sts').
        region_name: AWS region name.
        aws_access_key_id: Access key ID (required).
        aws_secret_access_key: Secret access key (required).
        aws_session_token: Optional session token for temporary credentials.

    Returns:
        Boto3 client for the specified service using ONLY the provided credentials.
    """
    # Handle FieldInfo objects (from pydantic)
    if hasattr(region_name, 'default') and region_name is not None:
        region_name = region_name.default

    if not aws_access_key_id or not aws_secret_access_key:
        raise ClientError('Missing AWS credentials: access key and secret key are required')

    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
        )
        return session.client(service_name, region_name=region_name, config=session_config)
    except Exception as e:
        msg = str(e)
        if 'ExpiredToken' in msg or 'ExpiredTokenException' in msg:
            raise ClientError('Your AWS credentials have expired. Please refresh them.')
        elif 'UnrecognizedClientException' in msg or 'SignatureDoesNotMatch' in msg:
            raise ClientError('AWS credentials are invalid. Please verify access key and secret key.')
        else:
            raise ClientError('Failed to create AWS client with provided credentials.')
