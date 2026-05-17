from io import BytesIO
from typing import BinaryIO
from uuid import uuid4

from miniopy_async import Minio
from miniopy_async.error import S3Error


class MinioService:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
    ):
        self.bucket_name = bucket_name

        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    async def ensure_bucket_exists(self):
        """
        Create bucket if not exists
        """
        exists = await self.client.bucket_exists(self.bucket_name)

        if not exists:
            await self.client.make_bucket(self.bucket_name)

    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload bytes file
        """

        data_stream = BytesIO(file_data)

        await self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=data_stream,
            length=len(file_data),
            content_type=content_type,
        )

        return object_name

    async def upload_uploadfile(
        self,
        file,
        folder: str = "uploads",
    ) -> str:
        """
        Upload FastAPI UploadFile
        """

        file_bytes = await file.read()

        ext = file.filename.split(".")[-1]

        object_name = f"{folder}/{uuid4()}.{ext}"

        await self.upload_file(
            file_data=file_bytes,
            object_name=object_name,
            content_type=file.content_type,
        )

        return object_name

    async def get_file_url(self, object_name: str, expires: int = 3600):
        """
        Generate presigned URL
        """

        url = await self.client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=expires,
        )

        return url

    async def delete_file(self, object_name: str):
        """
        Delete object
        """

        await self.client.remove_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
        )

    async def file_exists(self, object_name: str) -> bool:
        """
        Check object exists
        """

        try:
            await self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )

            return True

        except S3Error:
            return False

    async def download_file(self, object_name: str) -> bytes:
        """
        Download object as bytes
        """

        response = await self.client.get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
        )

        data = await response.read()

        await response.close()

        return data