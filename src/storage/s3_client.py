"""AWS S3 client for audio storage"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import os


class S3Client:
    """S3 client for audio file storage"""
    
    def __init__(
        self,
        bucket_name: str,
        region: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        if access_key and secret_key:
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        else:
            # Use default credentials
            self.s3_client = boto3.client('s3', region_name=region)
    
    def upload_audio(
        self,
        session_id: str,
        audio_data: bytes,
        timestamp: str
    ) -> str:
        """Upload audio file to S3"""
        # Generate S3 key with date-based path
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        key = f"{dt.year}/{dt.month:02d}/{dt.day:02d}/{session_id}.wav"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=audio_data,
                ContentType='audio/wav',
                ServerSideEncryption='AES256'
            )
            
            # Return S3 URL
            return f"s3://{self.bucket_name}/{key}"
        except ClientError as e:
            raise Exception(f"Failed to upload audio to S3: {e}")
    
    def download_audio(self, s3_url: str) -> bytes:
        """Download audio file from S3"""
        # Parse S3 URL
        if not s3_url.startswith("s3://"):
            raise ValueError("Invalid S3 URL")
        
        parts = s3_url[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1]
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download audio from S3: {e}")
    
    def delete_audio(self, s3_url: str) -> None:
        """Delete audio file from S3"""
        # Parse S3 URL
        if not s3_url.startswith("s3://"):
            raise ValueError("Invalid S3 URL")
        
        parts = s3_url[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1]
        
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
        except ClientError as e:
            raise Exception(f"Failed to delete audio from S3: {e}")
