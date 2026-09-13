"""Uji PDF generator pakai data ringkasan palsu.

Membuktikan alur template -> HTML -> PDF jalan, tanpa perlu LLM atau transkripsi.
Jalankan: python scripts/test_pdf_dummy.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.pdf_generator.pdf_generator_service import PDFGeneratorService

CONTEXT_SIMPLE = {
    "title": "Rapat Koordinasi Sprint 3",
    "audio_filename": "rapat-sprint-3.mp3",
    "generated_date": "6 September 2026",
    "language": "Indonesia",
    "duration": "42 menit",
    "summary": (
        "Tim membahas progres Sprint 3. Modul upload audio sudah selesai dan "
        "terhubung ke storage. Modul ringkasan masih menunggu kredensial LLM. "
        "Target rilis internal digeser satu minggu."
    ),
    "key_points": [
        "Endpoint upload audio sudah berfungsi end-to-end",
        "Integrasi MinIO berjalan tanpa Docker",
        "Kredensial LLM belum tersedia, jadi modul ringkasan tertunda",
        "Target rilis internal digeser ke minggu depan",
    ],
    "keywords": ["sprint 3", "upload", "storage", "LLM", "rilis"],
    "action_items": [
        {"pic": "Henny", "task": "Sambungkan summary generator ke LLM", "deadline": "12 Sep 2026"},
        {"pic": "Kaspul", "task": "Rapikan template PDF business", "deadline": "10 Sep 2026"},
        {"pic": "Andri", "task": "Siapkan kredensial DeepSeek", "deadline": "8 Sep 2026"},
    ],
}

CONTEXT_BUSINESS = {
    "title": "Rapat Koordinasi Sprint 3",
    "audio_filename": "rapat-sprint-3.mp3",
    "generated_date": "6 September 2026",
    "language": "Indonesia",
    "duration": "42 menit",
    "executive_summary": (
        "Sprint 3 berjalan sesuai rencana pada sisi backend storage, namun "
        "modul ringkasan terhambat ketersediaan kredensial LLM. Rilis internal "
        "diundur satu minggu tanpa mengubah lingkup pekerjaan."
    ),
    "key_discussion_points": [
        "Status modul upload audio dan integrasi storage",
        "Hambatan pada modul ringkasan otomatis",
        "Penyesuaian jadwal rilis internal",
    ],
    "decisions": [
        "Rilis internal digeser ke 19 September 2026",
        "Menggunakan DeepSeek sebagai penyedia LLM menggantikan Apilogy",
    ],
    "next_steps": [
        "Pengadaan kredensial DeepSeek",
        "Integrasi summary generator",
        "Uji end-to-end upload sampai PDF",
    ],
    "action_assignment": [
        {"pic": "Henny", "task": "Integrasi summary generator", "due_date": "12 Sep 2026", "notes": "Menunggu API key"},
        {"pic": "Kaspul", "task": "Finalisasi template PDF", "due_date": "10 Sep 2026", "notes": "-"},
        {"pic": "Andri", "task": "Pengadaan kredensial DeepSeek", "due_date": "8 Sep 2026", "notes": "Prioritas tinggi"},
    ],
}


def main() -> None:
    service = PDFGeneratorService()

    for template_type, context in (
        ("simple", CONTEXT_SIMPLE),
        ("business", CONTEXT_BUSINESS),
    ):
        path = service.generate_pdf(
            template_type=template_type,
            context=context,
            output_filename=f"dummy-{template_type}.pdf",
        )
        print(f"  OK  {template_type:9s} -> {path}")

    print("\nPDF generator jalan.")


if __name__ == "__main__":
    main()