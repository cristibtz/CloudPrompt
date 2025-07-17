import boto3
import logging

logger = logging.getLogger("aws_s3_tools_mcp")

def register_tools(mcp):

    @mcp.tool()
    async def create_s3_bucket():
        pass

    @mcp.tool()
    async def list_s3_buckets(
        region_name: str = "us-east-1",
        check_empty: bool = True
    ):
        """
        List S3 buckets with optional emptiness check
        """
        logger.info(f"Listing S3 buckets in region: {region_name}")
        s3 = boto3.client('s3', region_name=region_name)
        response = s3.list_buckets()

        buckets = []
        for bucket in response['Buckets']:
            bucket_info = {
                "Name": bucket['Name'],
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
                        
                except Exception as e:
                    logger.warning(f"Could not check emptiness for bucket {bucket['Name']}: {e}")
                    bucket_info["IsEmpty"] = "Unknown"
                    bucket_info["CanDelete"] = False
                    bucket_info["Error"] = str(e)
            
            buckets.append(bucket_info)
            
        logger.info(f"Found {len(buckets)} buckets in region {region_name}")
        return {"buckets": buckets}
    
    @mcp.tool()
    async def list_s3_bucket_objects():
        pass

    @mcp.tool()
    async def delete_s3_bucket(
        bucket_name: str,
        force: bool = False,
        region_name: str = "us-east-1"
    ):
        """
        Delete S3 bucket. Set force=True to empty the bucket first.
        """
        logger.info(f"Deleting S3 bucket: {bucket_name} in region {region_name}")
        s3 = boto3.client('s3', region_name=region_name)
        
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
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to delete bucket {bucket_name}: {error_msg}")
            
            if "not empty" in error_msg.lower():
                return {
                    "status": "error", 
                    "message": f"Bucket '{bucket_name}' is not empty. Use force=True to empty and delete."
                }
            
            return {"status": "error", "message": error_msg}
