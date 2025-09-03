import boto3
from botocore.exceptions import ClientError
import logging
from .auth_tools import get_aws_client, get_aws_session_region

logger = logging.getLogger("aws_s3_tools_mcp")

def register_tools(mcp):

    @mcp.tool()
    async def create_s3_bucket(
        bucket_name: str,
        session_id: str
    ):
        '''
        Create an S3 bucket in a specific region.
        REQUIRES: authenticate_aws must be called first to establish a session.
        
        :param bucket_name: str - Name of the S3 bucket to create.
        :param session_id: str - AWS session identifier from authenticate_aws.
        :return: Dict[str, str] - Information about the created bucket containing bucket_name and location.
        '''
        # Get authenticated S3 client
        s3 = get_aws_client('s3', session_id)
        if not s3:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_aws first."
            }
        
        region_name = get_aws_session_region(session_id)
        logger.info(f"Creating S3 bucket: {bucket_name} in region {region_name}")
        
        try:
            if region_name == "us-east-1":
                response = s3.create_bucket(Bucket=bucket_name)
            else:
                response = s3.create_bucket(
                    Bucket=bucket_name, 
                    CreateBucketConfiguration={'LocationConstraint': region_name}
                )               
            print(response['Location'])
            logger.info(f"Successfully created S3 bucket: {bucket_name}")

            return {"bucket_name": bucket_name, "location": response['Location']}

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Failed to create bucket {bucket_name}: {error_msg}")
            return {"status": "error", "message": error_msg}

    @mcp.tool()
    async def list_s3_buckets(
        session_id: str,
        check_empty: bool = False
    ):
        '''
        List all S3 buckets in a specific region.
        REQUIRES: authenticate_aws must be called first to establish a session.
        
        :param session_id: str - AWS session identifier from authenticate_aws.
        :param check_empty: bool - Whether to check if buckets are empty (default is False).
        :return: Dict[str, List[Dict[str, str]]] - List of buckets with their names, creation dates, and empty status.
        '''
        # Get authenticated S3 client
        s3 = get_aws_client('s3', session_id)
        if not s3:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_aws first."
            }
        
        region_name = get_aws_session_region(session_id)
        logger.info(f"Listing S3 buckets in region: {region_name}")

        try:
            response = s3.list_buckets(BucketRegion=region_name)
        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Failed to list buckets: {error_msg}")
            return {"status": "error", "message": error_msg}

        buckets = []
        for bucket in response['Buckets']:
            bucket_info = {
                "Name": bucket['Name'],
                "Region": bucket['BucketRegion'],
                "CreationDate": bucket['CreationDate'].isoformat()
            }
            
            if check_empty:
                try:
                    # Check if bucket is empty
                    objects = s3.list_objects_v2(Bucket=bucket['Name'], MaxKeys=1)
                    is_empty = 'Contents' not in objects
                    
                    bucket_info["IsEmpty"] = is_empty
                    bucket_info["CanDelete"] = is_empty
                    
                    if not is_empty:
                        # Count total objects (optional)
                        count_response = s3.list_objects_v2(Bucket=bucket['Name'])
                        object_count = count_response.get('KeyCount', 0)
                        bucket_info["ObjectCount"] = object_count
                    else:
                        bucket_info["ObjectCount"] = 0
                        
                except ClientError as e:
                    logger.warning(f"Could not check emptiness for bucket {bucket['Name']}: {e}")
                    bucket_info["IsEmpty"] = "Unknown"
                    bucket_info["CanDelete"] = False
                    bucket_info["Error"] = str(e)
            
            buckets.append(bucket_info)
            
        logger.info(f"Found {len(buckets)} buckets in region {region_name}")
        return {"buckets": buckets}
    
    @mcp.tool()
    async def list_s3_bucket_objects(
        bucket_name: str,
        session_id: str
    ):
        '''
        List all objects in a specific S3 bucket.
        REQUIRES: authenticate_aws must be called first to establish a session.
        
        :param bucket_name: str - Name of the S3 bucket to list objects from.
        :param session_id: str - AWS session identifier from authenticate_aws.
        :return: Dict[str, List[Dict[str, Union[str, int]]]] - List of objects with their keys and sizes.
        '''
        # Get authenticated S3 client
        s3 = get_aws_client('s3', session_id)
        if not s3:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_aws first."
            }
        
        region_name = get_aws_session_region(session_id)
        logger.info(f"Listing objects in S3 bucket: {bucket_name} in region {region_name}")
        
        try:
            response = s3.list_objects_v2(Bucket=bucket_name)
            if 'Contents' not in response:
                return {"objects": []}
            
            objects = []
            for obj in response['Contents']:
                objects.append({
                    'Key': obj['Key'],
                    'Size': obj['Size'],
                    'LastModified': obj['LastModified'].isoformat()
                })
                
            logger.info(f"Found {len(objects)} objects in bucket {bucket_name}")
            return {"objects": objects}
        
        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Failed to list objects in bucket {bucket_name}: {error_msg}")
            return {"status": "error", "message": error_msg}

    @mcp.tool()
    async def delete_s3_bucket_object(
        bucket_name: str,
        object_key: str,
        session_id: str
    ):
        '''
        Delete a specific object from an S3 bucket.
        REQUIRES: authenticate_aws must be called first to establish a session.
        
        :param bucket_name: str - Name of the S3 bucket.
        :param object_key: str - Key of the object to delete.
        :param session_id: str - AWS session identifier from authenticate_aws.
        :return: Dict[str, str] - Information about the deleted object or error message.
        '''
        # Get authenticated S3 client
        s3 = get_aws_client('s3', session_id)
        if not s3:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_aws first."
            }
        
        region_name = get_aws_session_region(session_id)
        logger.info(f"Deleting object {object_key} from S3 bucket: {bucket_name} in region {region_name}")
        
        try:
            try:
                s3.head_object(Bucket=bucket_name, Key=object_key)
                logger.info(f"Object {object_key} found in bucket {bucket_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.warning(f"Object {object_key} not found in bucket {bucket_name}")
                    return {
                        "status": "error", 
                        "message": f"Object '{object_key}' not found in bucket '{bucket_name}'"
                    }
                else:
                    raise e
            
            response = s3.delete_object(Bucket=bucket_name, Key=object_key)
        
            logger.info(f"Successfully deleted object {object_key} from bucket {bucket_name}")
            return {"deleted_object": object_key}
            
        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Failed to delete object {object_key} from bucket {bucket_name}: {error_msg}")
            return {"status": "error", "message": error_msg}

    @mcp.tool()
    async def delete_s3_bucket(
        bucket_name: str,
        session_id: str,
        force: bool = False
    ):
        '''
        Delete an S3 bucket. If force is True, it will empty the bucket before deletion.
        REQUIRES: authenticate_aws must be called first to establish a session.
        
        :param bucket_name: str - Name of the S3 bucket to delete.
        :param session_id: str - AWS session identifier from authenticate_aws.
        :param force: bool - Whether to force delete by emptying the bucket first (default is False).
        :return: Dict[str, str] - Information about the deleted bucket or error message.
        '''
        # Get authenticated S3 client
        s3 = get_aws_client('s3', session_id)
        if not s3:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_aws first."
            }
        
        region_name = get_aws_session_region(session_id)
        logger.info(f"Deleting S3 bucket: {bucket_name} in region {region_name}")
        
        try:
            if force:
                # Empty the bucket first
                logger.info(f"Force delete enabled - emptying bucket {bucket_name} first")
                
                # Delete all objects
                response = s3.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in response:
                    objects = [{'Key': obj['Key']} for obj in response['Contents']]
                    s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects}
                    )
                    logger.info(f"Deleted {len(objects)} objects from {bucket_name}")
            
            # Delete the bucket
            s3.delete_bucket(Bucket=bucket_name)
            logger.info(f"Successfully deleted S3 bucket: {bucket_name}")
            return {"deleted_bucket": bucket_name}
            
        except ClientError as e:
            error_msg = str(e)
            logger.error(f"Failed to delete bucket {bucket_name}: {error_msg}")
            
            if "not empty" in error_msg.lower():
                return {
                    "status": "error", 
                    "message": f"Bucket '{bucket_name}' is not empty. Use force=True to empty and delete."
                }
            
            return {"status": "error", "message": error_msg}
