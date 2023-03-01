from typing import Optional, List, Dict, Any

import boto3
from boto3 import Session
from boto3.s3.transfer import TransferConfig


class S3:
    CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session
        self.client = session.client("s3") if session else boto3.client("s3")

    def get_resource(self):
        return self.session.resource("s3") if self.session else boto3.resource("s3")

    @staticmethod
    def get_transfer_config(chunk_size: int = CHUNK_SIZE) -> TransferConfig:
        return TransferConfig(
            multipart_threshold=chunk_size,
            max_concurrency=10,
            multipart_chunksize=chunk_size,
            use_threads=True,
        )

    def list_buckets(self) -> List[Dict[str, Any]]:
        buckets = self.client.list_buckets()
        return buckets["Buckets"]

    def traverse(
        self, bucket: str, prefix: str = "", delimiter: str = ","
    ) -> List[str]:
        bucket = self.get_resource().Bucket(bucket)
        return [
            location.key
            for location in bucket.objects.filter(Delimiter=delimiter, Prefix=prefix)
        ]

    def list_objects(
        self, bucket: str, prefix: str = "", delimiter: str = ","
    ) -> List[str]:
        location_index = len(prefix.split("/"))
        return sorted(
            list(
                set(
                    [
                        location.split("/")[location_index]
                        for location in self.traverse(bucket, prefix, delimiter)
                    ]
                )
            )
        )

    def list_objects_v2(
        self, bucket: str, prefix: str = "", delimiter: str = ","
    ) -> List[str]:
        location_index = len(prefix.split("/"))
        return sorted(
            list(
                set(
                    [
                        location.split("/")[location_index]
                        for location in self.traverse(bucket, prefix, delimiter)
                        if location_index < len(location.split("/"))
                    ]
                )
            )
        )

    def copy(self, bucket: str, source_key: str, target_bucket: str, target_key: str):
        self.client.copy_object(
            CopySource={"Bucket": bucket, "Key": source_key},
            Bucket=target_bucket,
            Key=target_key,
        )

    def delete_objects_with_prefix(self, bucket: str, prefix: str) -> None:
        objects = self.list_objects(bucket, prefix)
        self.delete_objects(bucket, objects)

    def delete_object(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

    def delete_objects(self, bucket: str, keys: List[str]) -> None:
        object_keys = [{"Key": key} for key in keys]
        partition_size = 500
        for i in range(0, len(object_keys), partition_size):
            partition = object_keys[i : i + partition_size]
            print(f"Deleting {partition_size} objects from s3")
            self.client.delete_objects(Bucket=bucket, Delete={"Objects": partition})

    def create_bucket(self, bucket_name: str) -> Dict[str, Any]:
        return self.client.create_bucket(Bucket=bucket_name)

    def download_file(
        self, bucket: str, key: str, download_path: str, chunk_size: int = CHUNK_SIZE
    ) -> None:
        resource = self.get_resource()
        transfer_config = S3.get_transfer_config(chunk_size)
        bucket = resource.Bucket(bucket)
        bucket.download_file(key, download_path, Config=transfer_config)

    def download_file_to_fileobj(
        self, bucket: str, key: str, file, chunk_size: int = CHUNK_SIZE
    ) -> None:
        resource = self.get_resource()
        transfer_config = S3.get_transfer_config(chunk_size)
        bucket = resource.Bucket(bucket)
        bucket.download_fileobj(key, file, Config=transfer_config)
        file.flush()

    def download_as_obj(self, bucket: str, key: str):
        return self.client.get_object(Bucket=bucket, Key=key)

    def upload_object(self, bucket: str, key: str, file_destination: str) -> None:
        resource = self.get_resource()
        transfer_config = S3.get_transfer_config(self.CHUNK_SIZE)
        bucket = resource.Bucket(bucket)
        bucket.upload_file(file_destination, key, Config=transfer_config)

    def upload_file(self, bucket: str, key: str, file) -> None:
        self.client.upload_fileobj(file, bucket, key)

    def upload_large_file(
        self,
        bucket: str,
        key: str,
        file_destination: str,
        metadata: Optional[dict] = None,
        chunk_size=CHUNK_SIZE,
    ):
        print(f"Uploading file {file_destination} to bucket {bucket}, key {key}")

        transfer_config = self.get_transfer_config(chunk_size)
        args = {"ACL": "bucket-owner-full-control"}.update(metadata or {})
        resource = self.get_resource()
        bucket = resource.Bucket(bucket)
        bucket.upload_file(
            file_destination, key, ExtraConfig=args, Config=transfer_config
        )
    
    
