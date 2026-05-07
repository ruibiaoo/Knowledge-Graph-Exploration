from pathlib import Path
import boto3

s3 = boto3.client("s3")


def download_from_s3(bucket: str, key: str, local_path: str) -> None:
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, local_path)


def upload_to_s3(local_path: str, bucket: str, key: str) -> None:
    s3.upload_file(local_path, bucket, key)


def list_s3_files(bucket: str, prefix: str) -> list[str]:
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    files = []
    for item in response.get("Contents", []):
        key = item["Key"]
        if not key.endswith("/"):
            files.append(key)

    return files