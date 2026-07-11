import os

class S3StorageClient:
    """
    Client wrapper for uploading artifacts (resumes, screenshots) to AWS S3.
    """
    
    @staticmethod
    def upload_file(local_path: str, bucket_name: str, object_name: str) -> str:
        if not os.path.exists(local_path):
            return ""
        # Mocking Boto3 client upload
        # In production: boto3.client('s3').upload_file(local_path, bucket_name, object_name)
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        return s3_url
