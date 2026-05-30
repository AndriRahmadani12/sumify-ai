from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.core.exceptions import ProcessingException
from src.services.pdf_templates.pdf_template_handler import PDFTemplateHandler


class PDFGeneratorService:
    """Generates summary PDFs from rendered HTML templates."""

    def __init__(
        self,
        template_handler: PDFTemplateHandler | None = None,
        output_dir: Path | str = "generated_pdfs",
    ) -> None:
        self.template_handler = template_handler or PDFTemplateHandler()
        self.output_dir = Path(output_dir)

    def render_html(self, template_type: str, context: dict[str, Any]) -> str:
        return self.template_handler.render(template_type, context)

    def generate_pdf(
        self,
        template_type: str,
        context: dict[str, Any],
        output_filename: str | None = None,
    ) -> Path:
        html = self.render_html(template_type, context)
        return self.generate_pdf_from_html(html, output_filename)

    def generate_pdf_from_html(
        self,
        html: str,
        output_filename: str | None = None,
    ) -> Path:
        output_path = self._build_output_path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise ProcessingException(
                "PDF generation requires the 'weasyprint' package to be installed."
            ) from exc

        HTML(string=html).write_pdf(str(output_path))
        return output_path

    def _build_output_path(self, output_filename: str | None) -> Path:
        filename = (
            Path(output_filename).name
            if output_filename
            else f"summary-{uuid4().hex}.pdf"
        )

        if not filename.endswith(".pdf"):
            filename = f"{filename}.pdf"

        return self.output_dir / filename
