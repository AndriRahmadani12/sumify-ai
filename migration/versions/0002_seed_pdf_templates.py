"""Seed database-backed PDF templates.

Revision ID: 0002_seed_pdf_templates
Revises: 0001_initial
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_seed_pdf_templates"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SIMPLE_SUMMARY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{{title}}</title>
  <style>
    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: #111827;
      background: #ffffff;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 11px;
      line-height: 1.45;
    }

    .document { width: 100%; }

    .title {
      font-size: 22px;
      font-weight: 700;
      line-height: 1.2;
      margin: 0 0 18px;
      text-align: center;
    }

    .meta-table {
      border-collapse: collapse;
      margin: 0 0 28px;
      width: 100%;
    }

    .meta-table td {
      border: 0;
      padding: 2px 4px 5px 0;
      vertical-align: top;
    }

    .meta-label {
      font-weight: 700;
      width: 30%;
    }

    .meta-value { width: 70%; }

    .section {
      margin: 0 0 18px;
      page-break-inside: avoid;
    }

    h2 {
      color: #111827;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.25;
      margin: 0 0 7px;
    }

    .section-body {
      margin-left: 16px;
      text-align: justify;
      text-justify: inter-word;
    }

    ul, ol {
      margin: 0;
      padding-left: 16px;
    }

    li {
      margin-bottom: 4px;
      text-align: justify;
      text-justify: inter-word;
    }

    .keywords {
      margin-left: 16px;
      word-break: break-word;
    }
  </style>
</head>
<body>
  <main class="document">
    <h1 class="title">{{title}}</h1>

    <table class="meta-table">
      <tbody>
        <tr><td class="meta-label">Generated Date</td><td class="meta-value">: {{generated_date}}</td></tr>
        <tr><td class="meta-label">Audio File</td><td class="meta-value">: {{audio_filename}}</td></tr>
        <tr><td class="meta-label">Duration</td><td class="meta-value">: {{duration}}</td></tr>
        <tr><td class="meta-label">Language</td><td class="meta-value">: {{language}}</td></tr>
      </tbody>
    </table>

    <section class="section">
      <h2>1. Summary</h2>
      <div class="section-body">{{summary}}</div>
    </section>

    <section class="section">
      <h2>2. Key Points</h2>
      <div class="section-body"><ul>{{key_points}}</ul></div>
    </section>

    <section class="section">
      <h2>3. Action Items</h2>
      <div class="section-body"><ul>{{action_items}}</ul></div>
    </section>

    <section class="section">
      <h2>4. Keywords</h2>
      <div class="keywords">{{keywords}}</div>
    </section>
  </main>
</body>
</html>"""


BUSINESS_SUMMARY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{{title}}</title>
  <style>
    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: #111827;
      background: #ffffff;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 11px;
      line-height: 1.45;
    }

    .document { width: 100%; }

    .title {
      font-size: 22px;
      font-weight: 700;
      line-height: 1.2;
      margin: 0 0 18px;
      text-align: center;
    }

    .meta-table {
      border-collapse: collapse;
      margin: 0 0 26px;
      width: 100%;
    }

    .meta-table td {
      border: 0;
      padding: 2px 4px 5px 0;
      vertical-align: top;
    }

    .meta-label {
      font-weight: 700;
      width: 30%;
    }

    .meta-value { width: 70%; }

    .section {
      margin: 0 0 17px;
      page-break-inside: avoid;
    }

    .table-section {
      break-inside: auto;
      page-break-inside: auto;
    }

    h2 {
      color: #111827;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.25;
      margin: 0 0 7px;
    }

    .section-body {
      margin-left: 16px;
      text-align: justify;
      text-justify: inter-word;
    }

    ul, ol {
      margin: 0;
      padding-left: 16px;
    }

    li {
      margin-bottom: 4px;
      text-align: justify;
      text-justify: inter-word;
    }

    .pic-table {
      border-collapse: collapse;
      margin-top: 5px;
      width: 100%;
    }

    .pic-table th,
    .pic-table td {
      border: 1px solid #d1d5db;
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
    }

    .pic-table thead { display: table-header-group; }

    .pic-table tr {
      break-inside: avoid;
      page-break-inside: avoid;
    }

    .pic-table th {
      background: #f3f4f6;
      font-weight: 700;
      text-align: center;
    }

    .pic-table th:nth-child(1) { width: 22%; }
    .pic-table th:nth-child(2) { width: 38%; }
    .pic-table th:nth-child(3) { width: 18%; }
    .pic-table th:nth-child(4) { width: 22%; }

    .empty-state {
      color: #6b7280;
      font-style: italic;
      text-align: center;
    }
  </style>
</head>
<body>
  <main class="document">
    <h1 class="title">{{title}}</h1>

    <table class="meta-table">
      <tbody>
        <tr><td class="meta-label">Generated Date</td><td class="meta-value">: {{generated_date}}</td></tr>
        <tr><td class="meta-label">Audio File</td><td class="meta-value">: {{audio_filename}}</td></tr>
        <tr><td class="meta-label">Duration</td><td class="meta-value">: {{duration}}</td></tr>
        <tr><td class="meta-label">Language</td><td class="meta-value">: {{language}}</td></tr>
      </tbody>
    </table>

    <section class="section">
      <h2>1. Executive Summary</h2>
      <div class="section-body">{{executive_summary}}</div>
    </section>

    <section class="section">
      <h2>2. Key Discussion Points</h2>
      <div class="section-body"><ul>{{key_discussion_points}}</ul></div>
    </section>

    <section class="section">
      <h2>3. Decisions</h2>
      <div class="section-body"><ul>{{decisions}}</ul></div>
    </section>

    <section class="section">
      <h2>4. Next Steps</h2>
      <div class="section-body"><ul>{{next_steps}}</ul></div>
    </section>

    <section class="section table-section">
      <h2>5. Action Assignment (PIC Table)</h2>
      <table class="pic-table">
        <thead>
          <tr><th>PIC</th><th>Task</th><th>Due Date</th><th>Notes</th></tr>
        </thead>
        <tbody>{{action_assignment}}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"""


TEMPLATES = (
    ("Simple Summary", SIMPLE_SUMMARY_HTML),
    ("Business Summary", BUSINESS_SUMMARY_HTML),
)


def upgrade() -> None:
    connection = op.get_bind()

    for name, html_content in TEMPLATES:
        existing_id = connection.execute(
            sa.text(
                """
                SELECT id
                FROM pdf_templates
                WHERE name = :name
                ORDER BY id
                LIMIT 1
                """
            ),
            {"name": name},
        ).scalar_one_or_none()

        if existing_id is None:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO pdf_templates (name, html_content, is_active)
                    VALUES (:name, :html_content, true)
                    """
                ),
                {"name": name, "html_content": html_content},
            )
            continue

        connection.execute(
            sa.text(
                """
                UPDATE pdf_templates
                SET html_content = :html_content,
                    is_active = true
                WHERE id = :id
                """
            ),
            {"id": existing_id, "html_content": html_content},
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DELETE FROM pdf_templates
            WHERE name IN (:simple_name, :business_name)
            """
        ),
        {
            "simple_name": "Simple Summary",
            "business_name": "Business Summary",
        },
    )
