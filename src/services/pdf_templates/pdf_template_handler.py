from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from src.core.exceptions import ValidationException


@dataclass(frozen=True)
class PDFTemplate:
    id: str
    name: str
    directory: str


class PDFTemplateHandler:
    """Selects PDF templates and renders their HTML content."""

    _templates: dict[str, PDFTemplate] = {
        "simple": PDFTemplate(
            id="simple",
            name="Simple Summary",
            directory="simple_summary",
        ),
        "business": PDFTemplate(
            id="business",
            name="Business Summary",
            directory="business_summary",
        ),
        "study": PDFTemplate(
            id="study",
            name="Study Summary",
            directory="study_summary",
        ),
    }
    _aliases: dict[str, str] = {
        "simple_summary": "simple",
        "business_summary": "business",
        "study_summary": "study",
    }

    def __init__(self, templates_dir: Path | None = None) -> None:
        self.templates_dir = templates_dir or Path(__file__).resolve().parent

    def list_templates(self) -> list[dict[str, str]]:
        return [
            {"id": template.id, "name": template.name}
            for template in self._templates.values()
        ]

    def render(self, template_type: str, context: dict[str, Any]) -> str:
        template = self._get_template(template_type)
        template_html = self._read_template_file(template)
        rendered_context = self._normalize_context(context)

        for key, value in rendered_context.items():
            template_html = template_html.replace(f"{{{{{key}}}}}", value)

        return self._clear_unresolved_placeholders(template_html)

    def _get_template(self, template_type: str) -> PDFTemplate:
        normalized_type = template_type.strip().lower()
        normalized_type = self._aliases.get(normalized_type, normalized_type)
        template = self._templates.get(normalized_type)

        if template is None:
            raise ValidationException(
                message="Unsupported PDF template type",
                details={
                    "template_type": template_type,
                    "available_templates": list(self._templates.keys()),
                },
            )

        return template

    def _read_template_file(self, template: PDFTemplate) -> str:
        template_path = self.templates_dir / template.directory / "template.html"

        if not template_path.exists():
            raise ValidationException(
                message="PDF template file not found",
                details={"template": template.id, "path": str(template_path)},
            )

        return template_path.read_text(encoding="utf-8")

    def _normalize_context(self, context: dict[str, Any]) -> dict[str, str]:
        return {
            key: self._render_value(key, value)
            for key, value in context.items()
        }

    def _render_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, (list, tuple)):
            if key == "important_quotes":
                return "".join(
                    f"<blockquote>{escape(str(item))}</blockquote>"
                    for item in value
                )

            return "".join(
                f"<li>{escape(str(item))}</li>"
                for item in value
            )

        return escape(str(value))

    def _clear_unresolved_placeholders(self, template_html: str) -> str:
        rendered_html = template_html

        for placeholder in self._extract_placeholders(template_html):
            rendered_html = rendered_html.replace(placeholder, "")

        return rendered_html

    def _extract_placeholders(self, template_html: str) -> set[str]:
        placeholders: set[str] = set()
        cursor = 0

        while True:
            start = template_html.find("{{", cursor)
            if start == -1:
                break

            end = template_html.find("}}", start)
            if end == -1:
                break

            placeholders.add(template_html[start:end + 2])
            cursor = end + 2

        return placeholders
