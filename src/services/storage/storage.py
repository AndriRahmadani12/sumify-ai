"""Storage service abstraction."""

from dataclasses import dataclass
from uuid import uuid4

from src.core.storage.minio import MinioService
from src.core.config.setting import settings
from src.core.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FileUploadInfo:
    """File upload information."""
    filename: str
    content_type: str
    size: int
    storage_path: str
    storage_bucket: str


class StorageService:
    """Service for file storage operations.

    Provides a higher-level interface over the MinIO storage.
    """

    def __init__(self, storage: MinioService | None = None) -> None:
        """Initialize service.

        Args:
            storage: MinIO client instance.
        """
        self.storage = storage or MinioService(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket_name=settings.MINIO_BUCKET_NAME,
            secure=settings.MINIO_SECURE,
        )

    async def initialize(self) -> None:
        """Ensure bucket exists."""
        await self.storage.ensure_bucket_exists()

    async def upload_audio(
        self,
        file_data: bytes,
        filename: str,
        user_id: int,
        content_type: str = "audio/mpeg",
    ) -> FileUploadInfo:
        """Upload an audio file.

        Args:
            file_data: Raw file bytes.
            filename: Original filename.
            user_id: User ID for path organization.
            content_type: MIME type.

        Returns:
            File upload information.
        """
        # Generate unique path
        file_id = uuid4().hex
        extension = filename.split(".")[-1] if "." in filename else "bin"
        storage_path = f"meetings/{user_id}/{file_id}.{extension}"

        await self.storage.upload_file(
            file_data=file_data,
            object_name=storage_path,
            content_type=content_type,
        )

        logger.info(
            f"Audio file uploaded: path={storage_path}, size={len(file_data)}, user_id={user_id}"
        )

        return FileUploadInfo(
            filename=filename,
            content_type=content_type,
            size=len(file_data),
            storage_path=storage_path,
            storage_bucket=self.storage.bucket_name,
        )

    async def upload_pdf(
        self,
        file_data: bytes,
        meeting_id: int,
        filename: str = "summary.pdf",
    ) -> FileUploadInfo:
        """Upload a generated PDF file.

        Args:
            file_data: Raw PDF bytes.
            meeting_id: Meeting ID for path organization.
            filename: Original filename.

        Returns:
            File upload information.
        """
        storage_path = f"pdfs/{meeting_id}/{filename}"

        await self.storage.upload_file(
            file_data=file_data,
            object_name=storage_path,
            content_type="application/pdf",
        )

        logger.info(
            f"PDF file uploaded: meeting_id={meeting_id}, size={len(file_data)}"
        )

        return FileUploadInfo(
            filename=filename,
            content_type="application/pdf",
            size=len(file_data),
            storage_path=storage_path,
            storage_bucket=self.storage.bucket_name,
        )

    async def upload_from_fastapi(
        self,
        file,
        folder: str = "uploads",
        user_id: int | None = None,
    ) -> FileUploadInfo:
        """Upload FastAPI UploadFile.

        Args:
            file: FastAPI UploadFile object.
            folder: Folder path in storage.
            user_id: Optional user ID for path organization.

        Returns:
            File upload information.
        """
        if user_id:
            folder = f"meetings/{user_id}"

        object_name = await self.storage.upload_uploadfile(
            file=file,
            folder=folder,
        )

        file_bytes = await file.read()
        await file.seek(0)  # Reset file pointer

        logger.info(
            f"FastAPI file uploaded: path={object_name}, size={len(file_bytes)}"
        )

        return FileUploadInfo(
            filename=file.filename,
            content_type=file.content_type,
            size=len(file_bytes),
            storage_path=object_name,
            storage_bucket=self.storage.bucket_name,
        )

    async def get_file_url(
        self,
        storage_path: str,
        expiry: int = 3600,
    ) -> str:
        """Get presigned URL for file access.

        Args:
            storage_path: Path in storage.
            expiry: URL expiry in seconds.

        Returns:
            Presigned URL.
        """
        return await self.storage.get_file_url(
            object_name=storage_path,
            expires=expiry,
        )

    async def download_file(
        self,
        storage_path: str,
    ) -> bytes:
        """Download file from storage.

        Args:
            storage_path: Path in storage.

        Returns:
            File bytes.
        """
        return await self.storage.download_file(storage_path)

    async def delete_file(
        self,
        storage_path: str,
    ) -> None:
        """Delete file from storage.

        Args:
            storage_path: Path in storage.
        """
        await self.storage.delete_file(storage_path)
        logger.info(f"File deleted from storage: {storage_path}")

    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in storage.

        Args:
            storage_path: Path in storage.

        Returns:
            True if file exists, False otherwise.
        """
        return await self.storage.file_exists(storage_path)


# Singleton instance
storage_service = StorageService()
