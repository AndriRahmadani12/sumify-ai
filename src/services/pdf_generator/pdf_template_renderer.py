from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from typing import Any


class PDFTemplateRenderer:
    """Renders database-backed PDF template HTML with summary context."""

    _pic_table_keys = {"pic_table_rows", "pic_tasks", "pic_table", "pic_items"}
    _business_pic_table_keys = {
        "business_pic_table_rows",
        "business_pic_tasks",
        "business_pic_table",
        "business_pic_items",
    }
    _risk_keys = {"risks_open_questions", "risks_and_open_questions", "open_questions"}
    _pic_source_keys = ("pic_table_rows", "pic_tasks", "pic_table", "pic_items", "action_items")
    _business_pic_source_keys = (
        "business_pic_table_rows",
        "business_pic_tasks",
        "business_pic_table",
        "business_pic_items",
        "action_assignment",
        "pic_table_rows",
        "pic_tasks",
        "pic_table",
        "pic_items",
        "action_items",
    )
    _audio_filename_keys = (
        "audio_filename",
        "audio_file_name",
        "audio_file",
        "filename",
        "file_name",
        "original_filename",
        "source_file",
    )
    _logo_filename = "sumifyai_logo_horizontal.png"

    def __init__(self) -> None:
        self._logo_data_uri: str | None = None

    def render(self, html_content: str, context: dict[str, Any]) -> str:
        rendered_context = self._normalize_context(context)

        for key, value in rendered_context.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", value)

        return self._clear_unresolved_placeholders(html_content)

    def _normalize_context(self, context: dict[str, Any]) -> dict[str, str]:
        rendered_context = {
            key: self._render_value(key, value)
            for key, value in context.items()
        }

        if "pic_table_rows" not in rendered_context:
            rendered_context["pic_table_rows"] = self._render_pic_table_rows(
                self._get_pic_source(context)
            )

        if "business_pic_table_rows" not in rendered_context:
            rendered_context["business_pic_table_rows"] = self._render_business_pic_table_rows(
                self._get_business_pic_source(context)
            )

        if "action_assignment" not in rendered_context:
            rendered_context["action_assignment"] = self._render_action_assignment_rows(
                self._get_business_pic_source(context)
            )

        if "risks_open_questions" not in rendered_context:
            rendered_context["risks_open_questions"] = self._render_risks_open_questions(
                self._get_risks_open_questions_source(context)
            )

        rendered_context.setdefault("audio_filename", self._get_audio_filename(context))
        rendered_context.setdefault("generated_date", self._get_generated_date(context))
        rendered_context.setdefault("language", self._get_language(context))
        rendered_context.setdefault("language ", rendered_context["language"])
        rendered_context.setdefault("logo_src", self._get_logo_data_uri())

        return rendered_context

    def _render_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""

        if key in self._pic_table_keys:
            return self._render_pic_table_rows(value)

        if key in self._business_pic_table_keys:
            return self._render_business_pic_table_rows(value)

        if key == "action_assignment":
            return self._render_action_assignment_rows(value)

        if key in self._risk_keys:
            return self._render_risks_open_questions(value)

        if isinstance(value, (list, tuple)):
            if key == "important_quotes":
                return "".join(
                    f"<blockquote>{escape(str(item))}</blockquote>"
                    for item in value
                )

            return "".join(
                f"<li>{escape(str(self._render_list_item(item)))}</li>"
                for item in value
            )

        return escape(str(value))

    def _get_pic_source(self, context: dict[str, Any]) -> Any:
        for key in self._pic_source_keys:
            value = context.get(key)
            if value:
                return value

        return []

    def _get_business_pic_source(self, context: dict[str, Any]) -> Any:
        for key in self._business_pic_source_keys:
            value = context.get(key)
            if value:
                return value

        return []

    def _get_risks_open_questions_source(self, context: dict[str, Any]) -> Any:
        for key in ("risks_open_questions", "risks_and_open_questions", "open_questions"):
            value = context.get(key)
            if value:
                return value

        action_items = context.get("action_items")
        if not isinstance(action_items, (list, tuple)):
            return []

        risks = []
        for item in action_items:
            if not isinstance(item, dict):
                continue

            risk = self._first_present(
                item,
                (
                    "risks_open_questions",
                    "risks",
                    "risk",
                    "open_questions",
                    "questions",
                    "notes",
                ),
            )
            if risk:
                owner = self._first_present(item, ("pic", "PIC", "name", "person", "responsible", "owner"))
                risks.append({"owner": owner, "description": risk})

        return risks

    def _render_pic_table_rows(self, value: Any) -> str:
        if not value:
            return (
                '<tr><td colspan="3" class="empty-state">'
                "No PIC tasks available"
                "</td></tr>"
            )

        rows = value if isinstance(value, (list, tuple)) else [value]
        return "".join(self._render_pic_table_row(row) for row in rows)

    def _render_pic_table_row(self, row: Any) -> str:
        if isinstance(row, dict):
            pic = self._first_present(row, ("pic", "PIC", "person", "responsible", "owner"))
            task = self._first_present(row, ("task", "Task", "action", "item", "description"))
            deadline = self._first_present(row, ("deadline", "Deadline", "due_date", "due"))
        else:
            pic = ""
            task = row
            deadline = ""

        return (
            "<tr>"
            f"<td>{escape(str(pic or ''))}</td>"
            f"<td>{escape(str(task or ''))}</td>"
            f"<td>{escape(str(deadline or ''))}</td>"
            "</tr>"
        )

    def _render_business_pic_table_rows(self, value: Any) -> str:
        if not value:
            return (
                '<tr><td colspan="6" class="empty-state">'
                "No PIC tasks available"
                "</td></tr>"
            )

        rows = value if isinstance(value, (list, tuple)) else [value]
        return "".join(self._render_business_pic_table_row(row) for row in rows)

    def _render_business_pic_table_row(self, row: Any) -> str:
        if isinstance(row, dict):
            pic = self._first_present(row, ("pic", "PIC", "name", "person", "responsible", "owner"))
            position = self._first_present(row, ("position", "role", "title", "job_title"))
            task = self._first_present(row, ("task", "Task", "action", "item", "description"))
            deadline = self._first_present(row, ("deadline", "Deadline", "due_date", "due"))
            status = self._first_present(row, ("status", "Status", "progress"))
            priority = self._first_present(row, ("priority", "Priority", "urgency"))
        else:
            pic = ""
            position = ""
            task = row
            deadline = ""
            status = ""
            priority = ""

        return (
            "<tr>"
            f"<td>{escape(str(pic or '-'))}</td>"
            f"<td>{escape(str(position or '-'))}</td>"
            f"<td>{escape(str(task or ''))}</td>"
            f"<td>{escape(str(deadline or ''))}</td>"
            f"<td>{escape(str(status or ''))}</td>"
            f"<td>{escape(str(priority or ''))}</td>"
            "</tr>"
        )

    def _render_action_assignment_rows(self, value: Any) -> str:
        if not value:
            return (
                '<tr><td colspan="4" class="empty-state">'
                "No action assignments available"
                "</td></tr>"
            )

        rows = value if isinstance(value, (list, tuple)) else [value]
        return "".join(self._render_action_assignment_row(row) for row in rows)

    def _render_action_assignment_row(self, row: Any) -> str:
        if isinstance(row, dict):
            pic = self._first_present(row, ("pic", "PIC", "name", "person", "responsible", "owner"))
            task = self._first_present(row, ("task", "Task", "action", "item", "description"))
            due_date = self._first_present(row, ("due_date", "due", "deadline", "Deadline"))
            notes = self._first_present(row, ("notes", "note", "risks_open_questions"))
        else:
            pic = ""
            task = row
            due_date = ""
            notes = ""

        return (
            "<tr>"
            f"<td>{escape(str(pic or ''))}</td>"
            f"<td>{escape(str(task or ''))}</td>"
            f"<td>{escape(str(due_date or ''))}</td>"
            f"<td>{escape(str(notes or ''))}</td>"
            "</tr>"
        )

    def _render_risks_open_questions(self, value: Any) -> str:
        if not value:
            return '<li class="empty-state">No risks or open questions recorded</li>'

        items = value if isinstance(value, (list, tuple)) else [value]
        return "".join(
            f"<li>{escape(self._render_risk_item(item))}</li>"
            for item in items
        )

    def _render_risk_item(self, item: Any) -> str:
        if not isinstance(item, dict):
            return str(item)

        owner = self._first_present(item, ("owner", "pic", "PIC", "name", "person", "responsible"))
        description = self._first_present(
            item,
            ("description", "risk", "risks", "question", "open_question", "notes"),
        )

        if owner and description:
            return f"{owner}: {description}"

        return str(description or owner or item)

    def _render_list_item(self, item: Any) -> str:
        if not isinstance(item, dict):
            return str(item)

        pic = self._first_present(item, ("pic", "PIC", "person", "responsible", "owner"))
        task = self._first_present(item, ("task", "Task", "action", "item", "description"))
        deadline = self._first_present(item, ("deadline", "Deadline", "due_date", "due"))

        parts = []
        if task:
            parts.append(str(task))
        if pic:
            parts.append(f"PIC: {pic}")
        if deadline:
            parts.append(f"Deadline: {deadline}")

        return " | ".join(parts) if parts else str(item)

    def _first_present(self, data: dict[str, Any], keys: tuple[str, ...]) -> Any:
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value

        return ""

    def _get_audio_filename(self, context: dict[str, Any]) -> str:
        value = self._first_present(context, self._audio_filename_keys)
        return escape(str(value)) if value else "-"

    def _get_generated_date(self, context: dict[str, Any]) -> str:
        value = self._first_present(
            context,
            ("generated_date", "date", "created_at", "summary_date"),
        )
        return escape(str(value)) if value else "-"

    def _get_language(self, context: dict[str, Any]) -> str:
        value = self._first_present(context, ("language", "lang"))
        return escape(str(value)) if value else "-"

    def _get_logo_data_uri(self) -> str:
        if self._logo_data_uri is not None:
            return self._logo_data_uri

        logo_path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "logo"
            / self._logo_filename
        )

        if not logo_path.exists():
            self._logo_data_uri = ""
            return self._logo_data_uri

        encoded_logo = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        self._logo_data_uri = f"data:image/png;base64,{encoded_logo}"
        return self._logo_data_uri

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
