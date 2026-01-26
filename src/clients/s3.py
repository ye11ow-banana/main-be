import boto3


class S3Client:
    def __init__(self, region: str) -> None:
        self._region = region
        self._client = boto3.client("s3", region_name=region)

    def upload_avatar(
        self,
        file: bytes,
        bucket: str,
        key: str,
        content_type: str | None = None,
        cache_control: str = "public, max-age=31536000, immutable",
    ) -> str:
        extra_args = {"CacheControl": cache_control}
        if content_type:
            extra_args["ContentType"] = content_type

        self._client.put_object(Body=file, Bucket=bucket, Key=key, **extra_args)
        return self._get_public_url(bucket=bucket, key=key)

    def delete(self, bucket: str, key: str) -> None:
        self._client.delete_object(Bucket=bucket, Key=key)

    def _get_public_url(self, bucket: str, key: str) -> str:
        return f"https://{bucket}.s3.{self._region}.amazonaws.com/{key}"
