"""Router untuk membuat ulang PDF dari ringkasan yang sudah tersimpan.

Berguna kalau template diperbarui dan PDF lama perlu dicetak ulang tanpa
memanggil LLM lagi (hemat kuota).
"""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException

from src.core.logging.logger import get_logger
from src.services.pipeline.main_pipeline import (
    PipelineError,
    regenerate_pdf_from_summary,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pdf"])


@router.post("/meetings/{meeting_id}/regenerate-pdf")
async def regenerate_pdf(meeting_id: int, template_type: str = Form("simple")):
    """Cetak ulang PDF memakai ringkasan yang sudah ada di database."""
    try:
        pdf_path = await regenerate_pdf_from_summary(meeting_id, template_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Regenerate PDF gagal untuk meeting {meeting_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Gagal membuat PDF: {exc}") from exc

    return {
        "message": "PDF dibuat ulang dari ringkasan tersimpan",
        "meeting_id": meeting_id,
        "template_type": template_type,
        "pdf_path": str(pdf_path),
    }
