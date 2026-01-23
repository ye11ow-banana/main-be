from typing import IO

import boto3

from config import settings


class S3Client:
    def __init__(self) -> None:
        self._client = boto3.client("s3", region_name=settings.s3.region)

    def upload_file(self, file: IO[bytes], bucket: str, key: str) -> None:
        self._client.upload_fileobj(Fileobj=file, Bucket=bucket, Key=key)

    def get_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
