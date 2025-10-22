import logging
import pathlib

import boto3

from core import tp, unwrap_

for name in ["boto", "urllib3", "s3transfer", "boto3", "botocore", "nose"]:
    logging.getLogger(name).setLevel(logging.CRITICAL)


class S3Client:
    def __init__(self, base_enpoint: str, key: str, secret: str) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=base_enpoint,
            region_name="ams3",
            aws_access_key_id=key,
            aws_secret_access_key=secret,
        )

    def check_exist_file(self, bucket_name: str, file_name: str) -> bool:
        response = self._client.list_objects_v2(Bucket=bucket_name)
        if "Contents" not in response:
            return False

        files = unwrap_(response["Contents"])

        for file in files:
            if ("Key" in file) and (file_name == file["Key"]):
                return True

        return False

    def download_file(self, bucket_name: str, file_name: str) -> None:
        with pathlib.Path(file_name).open("wb") as file:
            self._client.download_fileobj(bucket_name, file_name, file)

    def upload_file(self, bucket_name: str, file_name: str) -> None:
        self._client.upload_file(file_name, bucket_name, file_name)

    def upload_fileobj(
        self, file: tp.BinaryIO, bucket_name: str, file_name: str
    ) -> None:
        self._client.upload_fileobj(file, bucket_name, file_name)
