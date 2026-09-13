"""Router untuk upload audio meeting."""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.core.database.postgree import async_session_maker
from src.core.logging.logger import get_logger
from src.repositories import MeetingRepository
from src.services.storage.storage import storage_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upload"])


@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    title: str | None = Form(None),
    language: str = Form("id"),
):
    """Terima file audio, simpan ke storage, lalu catat sebagai Meeting baru."""
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="File kosong")

    try:
        await storage_service.initialize()
        info = await storage_service.upload_audio(
            file_data=file_bytes,
            filename=file.filename,
            user_id=user_id,
            content_type=file.content_type or "audio/mpeg",
        )
    except Exception as exc:
        logger.error(f"Gagal upload ke storage: {exc}")
        raise HTTPException(status_code=502, detail="Gagal menyimpan file ke storage")

    async with async_session_maker() as session:
        repo = MeetingRepository(session)
        meeting = await repo.create(
            user_id=user_id,
            title=title or file.filename,
            description=file.filename,
            language=language,
            storage_path=info.storage_path,
            storage_bucket=info.storage_bucket,
        )

    return {
        "message": "Upload berhasil",
        "meeting_id": meeting.id,
        "status": meeting.status,
        "storage_path": info.storage_path,
        "size": info.size,
    }