from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.services.uploader.uploader import uploader_service, UploaderService


router = APIRouter(prefix="/transcribe", tags=["Transcribe"])


# Allowed audio MIME types
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",      # MP3
    "audio/wav",       # WAV
    "audio/x-wav",     # WAV (alternative)
    "audio/wave",      # WAVE
    "audio/mp4",       # M4A
    "audio/x-m4a",     # M4A (alternative)
    "audio/ogg",       # OGG
    "audio/webm",      # WebM
    "audio/flac",      # FLAC
    "audio/x-flac",    # FLAC (alternative)
}


async def get_uploader() -> UploaderService:
    """Dependency to get uploader service"""
    return uploader_service


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: int | None = None,
    uploader: UploaderService = Depends(get_uploader),
):
    """
    Upload audio file ke MinIO storage

    - **file**: File audio yang akan diupload (mp3, wav, m4a, ogg, flac, webm)
    - **user_id**: Optional user ID untuk organisasi folder

    Returns:
        - object_name: Nama object di MinIO
        - file_url: Presigned URL untuk akses file
        - filename: Nama asli file
        - content_type: MIME type file
        - size: Ukuran file dalam bytes
    """
    # Validate file type
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_AUDIO_TYPES)}"
        )

    # Validate file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4", ".wave"}
    file_ext = f".{file.filename.split('.')[-1].lower()}" if '.' in file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Ensure bucket exists
        await uploader.initialize()

        # Upload file
        result = await uploader.upload_audio(file, user_id=user_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "File uploaded successfully",
                "data": result,
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.delete("/delete/{object_name:path}")
async def delete_audio(
    object_name: str,
    uploader: UploaderService = Depends(get_uploader),
):
    """
    Delete audio file dari MinIO storage

    - **object_name**: Nama object di MinIO (path lengkap, contoh: audio/uuid.mp3)
    """
    try:
        await uploader.delete_audio(object_name)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"File {object_name} deleted successfully",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/url/{object_name:path}")
async def get_audio_url(
    object_name: str,
    expires: int = 3600,
    uploader: UploaderService = Depends(get_uploader),
):
    """
    Get presigned URL untuk audio file

    - **object_name**: Nama object di MinIO
    - **expires**: Waktu kedaluwarsa URL dalam detik (default: 3600)
    """
    try:
        url = await uploader.get_audio_url(object_name, expires)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "object_name": object_name,
                    "file_url": url,
                    "expires_in": expires,
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate URL: {str(e)}"
        )
