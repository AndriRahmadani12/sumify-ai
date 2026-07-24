from __future__ import annotations

import asyncio
from pathlib import Path

from src.core.database.postgree import async_session_maker
from src.repositories.pdf_template import PDFTemplateRepository
from src.services.pdf_generator.pdf_generator_service import PDFGeneratorService


def build_context() -> dict:
    return {
        "title": "Alphabet Inc. Annual Shareholder Meeting",
        "date": "2026-06-18",
        "language": "Bahasa Indonesia",
        "audio_filename": "alphabet-annual-shareholder-meeting-2026-recording.mp3",
        "duration": "1 jam 24 menit",
        "participants": (
            "Sundar Pichai, Ruth Porat, John L. Hennessy, Investor Relations Team, "
            "Board Representatives, Shareholders"
        ),
        "summary": (
            "Rapat pemegang saham tahunan membahas kinerja Alphabet selama tahun fiskal terakhir, "
            "prioritas investasi pada AI dan infrastruktur komputasi, perkembangan Google Cloud, "
            "serta pendekatan perusahaan terhadap disiplin biaya dan tata kelola. Manajemen "
            "menjelaskan bahwa fokus utama tahun berjalan adalah memperluas manfaat AI ke produk "
            "inti, menjaga pertumbuhan pendapatan yang sehat, dan memastikan kepatuhan terhadap "
            "regulasi global. Pemegang saham mengajukan pertanyaan terkait belanja modal, risiko "
            "antitrust, privasi data, dan transparansi dalam pengembangan AI."
        ),
        "executive_summary": (
            "Manajemen menyampaikan bahwa Alphabet tetap berada pada posisi keuangan yang kuat "
            "dan akan melanjutkan investasi strategis pada AI, Google Cloud, Search, YouTube, "
            "dan infrastruktur data center. Dewan menekankan bahwa pertumbuhan jangka panjang "
            "harus diseimbangkan dengan pengendalian biaya, pengawasan risiko regulasi, dan "
            "praktik AI yang bertanggung jawab. Rapat menghasilkan beberapa tindak lanjut terkait "
            "komunikasi investor, pelaporan risiko, dan metrik pengawasan AI."
        ),
        "key_points": [
            "Alphabet menempatkan AI sebagai prioritas strategis lintas Search, Workspace, Cloud, YouTube, dan perangkat developer.",
            "Belanja modal akan tetap tinggi untuk mendukung data center, model AI, dan kapasitas komputasi global.",
            "Google Cloud disebut sebagai salah satu area pertumbuhan utama dengan fokus pada pelanggan enterprise.",
            "Pemegang saham meminta transparansi yang lebih jelas mengenai risiko regulasi, privasi, dan penggunaan data.",
            "Dewan menegaskan peran komite audit dan governance dalam mengawasi risiko AI dan kepatuhan.",
        ],
        "key_discussion_points": [
            "Kinerja Search dan iklan digital tetap menjadi fondasi pendapatan, sementara AI digunakan untuk meningkatkan kualitas produk.",
            "Google Cloud dibahas sebagai pilar pertumbuhan jangka panjang, terutama untuk workload AI dan layanan data enterprise.",
            "Manajemen menjelaskan bahwa kenaikan capex terutama berkaitan dengan data center, TPU, dan kapasitas komputasi.",
            "Pemegang saham menanyakan strategi perusahaan dalam menghadapi pengawasan antitrust di Amerika Serikat dan Eropa.",
            "Dewan membahas pentingnya governance untuk AI safety, privasi data, keamanan model, dan evaluasi dampak sosial.",
            "Investor Relations diminta memperjelas narasi capital allocation dalam materi kuartalan berikutnya.",
        ],
        "decisions": [
            "Menyiapkan investor memo yang menjelaskan arah capex AI, data center, dan Google Cloud.",
            "Memperbarui risk register dengan penekanan pada antitrust, privasi data, AI governance, dan model safety.",
            "Menambahkan penjelasan capital allocation pada materi earnings call berikutnya.",
            "Menyertakan ringkasan metrik pengawasan AI dalam laporan governance tahunan.",
        ],
        "action_items": [
            {
                "pic": "Jim Friedland",
                "position": "Director, Investor Relations",
                "task": "Mendistribusikan ringkasan Q&A rapat kepada pemegang saham institusional",
                "deadline": "2026-06-25",
                "notes": "Menunggu final review dari Board Secretary sebelum distribusi eksternal.",
            },
            {
                "pic": "Ruth Porat",
                "position": "President & Chief Investment Officer",
                "task": "Menyiapkan memo capital allocation terkait capex AI, data center, buyback, dan cash reserve",
                "deadline": "2026-07-02",
                "notes": "Perlu konfirmasi asumsi capex terbaru dan sensitivitas margin.",
            },
            {
                "pic": "Kent Walker",
                "position": "President, Global Affairs & Chief Legal Officer",
                "task": "Memperbarui risk register untuk antitrust, privasi data, dan kepatuhan AI global",
                "deadline": "2026-07-09",
                "notes": "Beberapa perkara regulasi masih berubah dan perlu monitoring mingguan.",
            },
            {
                "pic": "James Manyika",
                "position": "SVP, Research, Technology & Society",
                "task": "Menyusun metrik pengawasan AI untuk laporan governance tahunan",
                "deadline": "2026-07-16",
                "notes": "Belum disepakati metrik final untuk model evaluation dan incident reporting.",
            },
        ],
        "next_steps": [
            "Finalisasi minutes of meeting setelah review Board Secretary.",
            "Kirim follow-up deck kepada pemegang saham institusional dan analis utama.",
            "Masukkan pembaruan AI governance ke materi laporan tahunan berikutnya.",
            "Siapkan talking points untuk earnings call berikutnya terkait capex dan cloud growth.",
        ],
        "keywords": "Alphabet, shareholder meeting, AI investment, Google Cloud, capex, governance, antitrust, privacy",
        "main_topic": "Alphabet shareholder review on AI strategy, capital allocation, governance, and regulatory risk",
        "detailed_summary": (
            "Rapat dibuka oleh Board Chair dengan penjelasan agenda, tata tertib pemungutan suara, "
            "dan prioritas governance. CEO kemudian memaparkan arah strategis Alphabet, terutama "
            "integrasi AI ke Search, Workspace, Cloud, YouTube, dan platform developer. CFO "
            "menjelaskan bahwa perusahaan mempertahankan posisi kas yang kuat, namun tetap "
            "menerapkan disiplin biaya untuk memastikan investasi infrastruktur AI memberikan "
            "nilai jangka panjang. Pada sesi tanya jawab, pemegang saham menyoroti kenaikan capex, "
            "risiko antitrust, penggunaan data untuk pelatihan model, dan transparansi pelaporan "
            "AI governance. Manajemen menyetujui tindak lanjut untuk memperjelas komunikasi investor, "
            "memperbarui risk register, dan menambahkan metrik pengawasan AI pada laporan governance."
        ),
        "key_concepts": [
            "AI-first product strategy",
            "Capital allocation discipline",
            "Cloud and data center scalability",
            "Antitrust and privacy risk",
            "Board-level AI governance",
            "Investor transparency",
        ],
        "timeline_highlights": [
            "Board Chair membuka rapat, menetapkan agenda, dan menjelaskan prosedur voting.",
            "CEO menyampaikan strategi AI-first serta prioritas untuk Search, Cloud, dan YouTube.",
            "CFO menjelaskan capex, margin, buyback, dan pendekatan capital allocation.",
            "Pemegang saham mengajukan pertanyaan tentang antitrust, privasi, data usage, dan AI safety.",
            "Manajemen menyetujui tindak lanjut untuk investor communication dan governance reporting.",
        ],
        "important_quotes": [
            "AI remains one of the most important long-term opportunities across our products and platforms.",
            "We will continue to balance long-term investment with discipline, accountability, and transparency.",
            "Trust, safety, and responsible development are central to how we bring AI to users and customers.",
        ],
    }


async def main() -> None:
    output_dir = Path("generated_pdfs")
    output_dir.mkdir(exist_ok=True)

    context = build_context()

    async with async_session_maker() as session:
        repository = PDFTemplateRepository(session)
        service = PDFGeneratorService(repository, output_dir=output_dir)

        for template_name in ("Business Summary", "Simple Summary"):
            template = await repository.get_by_name(template_name)
            if template is None:
                print(f"Template tidak ditemukan di database: {template_name}")
                continue

            pdf_name = f"coba-{template.id}.pdf"

            try:
                pdf_path = await service.generate_pdf(
                    template.id,
                    context,
                    pdf_name,
                )
            except Exception as exc:
                print(f"PDF gagal dibuat untuk template_id={template.id}: {exc}")
            else:
                print(f"PDF dibuat: {pdf_path}")


if __name__ == "__main__":
    asyncio.run(main())
