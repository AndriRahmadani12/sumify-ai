from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.core.exceptions import NotFoundException, ValidationException
from src.services.pdf_generator import PDFGeneratorService, PDFTemplateRenderer


class FakePDFTemplateRepository:
    def __init__(self, template: SimpleNamespace | None) -> None:
        self.template = template
        self.requested_ids: list[int] = []

    async def get_by_id(self, template_id: int) -> SimpleNamespace | None:
        self.requested_ids.append(template_id)
        return self.template


class PDFGeneratorServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_render_html_uses_database_template_id_and_content(self) -> None:
        repository = FakePDFTemplateRepository(
            SimpleNamespace(
                id=7,
                html_content="<h1>{{title}}</h1><ul>{{key_points}}</ul>",
                is_active=True,
            )
        )
        service = PDFGeneratorService(repository)  # type: ignore[arg-type]

        html = await service.render_html(
            7,
            {
                "title": "Rapat <Penting>",
                "key_points": ["Keputusan A", "Keputusan B"],
            },
        )

        self.assertEqual(repository.requested_ids, [7])
        self.assertIn("<h1>Rapat &lt;Penting&gt;</h1>", html)
        self.assertIn("<li>Keputusan A</li>", html)
        self.assertNotIn("{{", html)

    async def test_render_html_rejects_missing_template(self) -> None:
        service = PDFGeneratorService(
            FakePDFTemplateRepository(None)  # type: ignore[arg-type]
        )

        with self.assertRaises(NotFoundException):
            await service.render_html(404, {})

    async def test_render_html_rejects_inactive_template(self) -> None:
        repository = FakePDFTemplateRepository(
            SimpleNamespace(id=3, html_content="<p>{{summary}}</p>", is_active=False)
        )
        service = PDFGeneratorService(repository)  # type: ignore[arg-type]

        with self.assertRaises(ValidationException):
            await service.render_html(3, {"summary": "Tidak dipakai"})

    async def test_render_html_rejects_empty_database_content(self) -> None:
        repository = FakePDFTemplateRepository(
            SimpleNamespace(id=9, html_content="  ", is_active=True)
        )
        service = PDFGeneratorService(repository)  # type: ignore[arg-type]

        with self.assertRaises(ValidationException):
            await service.render_html(9, {})


class PDFTemplateRendererTests(unittest.TestCase):
    def test_renderer_builds_action_assignment_rows(self) -> None:
        renderer = PDFTemplateRenderer()

        html = renderer.render(
            "<table><tbody>{{action_assignment}}</tbody></table>",
            {
                "action_assignment": [
                    {
                        "pic": "Ayu",
                        "task": "Kirim laporan",
                        "due_date": "2026-07-30",
                        "notes": "Final review",
                    }
                ]
            },
        )

        self.assertIn("<td>Ayu</td>", html)
        self.assertIn("<td>Kirim laporan</td>", html)
        self.assertIn("<td>2026-07-30</td>", html)
        self.assertIn("<td>Final review</td>", html)


if __name__ == "__main__":
    unittest.main()
