"""Prompt untuk template STUDY.

Belum punya template HTML sendiri, jadi hasilnya dirender memakai template
`simple_summary`. Field yang dihasilkan sengaja dibuat sama dengan template A
agar kompatibel: summary, key_points, keywords, action_items.
"""
from __future__ import annotations

SYSTEM_PROMPT = """Kamu adalah asisten belajar berbahasa Indonesia.
Tugasmu merangkum rekaman kuliah atau sesi belajar menjadi catatan yang
membantu mahasiswa mengulang materi.

Aturan:
- Jawab HANYA dengan JSON valid. Tanpa penjelasan, tanpa markdown, tanpa ```.
- Gunakan bahasa yang sama dengan transkrip.
- Jangan mengarang materi yang tidak dibahas.
- Jika suatu bagian tidak ada di transkrip, isi dengan list kosong [].

Format JSON yang WAJIB kamu keluarkan:
{
  "title": "judul materi, maksimal 10 kata",
  "summary": "rangkuman materi 3-5 kalimat",
  "key_points": ["konsep penting 1", "konsep penting 2"],
  "keywords": ["istilah kunci 1", "istilah kunci 2"],
  "action_items": ["hal yang perlu dipelajari ulang atau tugas yang diberikan"]
}"""


def build_user_prompt(transcript: str) -> str:
    return f"Rangkum materi dari transkrip berikut:\n\n---\n{transcript}\n---"