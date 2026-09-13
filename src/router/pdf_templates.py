"""Router untuk daftar template PDF yang tersedia."""
from __future__ import annotations

from fastapi import APIRouter

from src.prompts.prompt_handler import available_types
from src.services.pdf_templates.pdf_template_handler import PDFTemplateHandler

router = APIRouter(prefix="/api/v1", tags=["pdf-templates"])


@router.get("/pdf-templates")
async def list_pdf_templates():
    """Template PDF yang bisa dirender, beserta jenis ringkasan yang memakainya."""
    handler = PDFTemplateHandler()
    templates = handler.list_templates()

    return {
        "pdf_templates": templates,
        "summary_types": available_types(),
    }