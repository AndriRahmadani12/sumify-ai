# Sumify AI: Meeting Summarizer

<p align="center">
  <img src="docs\logo\sumifyai_logo_horizontal.png" alt="Sumify AI" width="420" />
</p>

Aplikasi untuk meringkas hasil rapat dari file audio menggunakan AI. Aplikasi ini mengubah audio menjadi teks (transkripsi), lalu menghasilkan ringkasan dan dokumen PDF.

## Repository Terkait
Project ini merupakan repository untuk aplikasi Android atau tampilan user Sumify AI.

[![Mobile App Repository](https://img.shields.io/badge/Mobile%20App%20Repository-sumify--ai-181717?style=for-the-badge&logo=github)]([https://github.com/AndriRahmadani12/sumify-ai](https://github.com/mkaspulanwar/sumify-ai-fe))

## Tim
| Nama | GitHub |
| --- | --- |
| M. Kaspul Anwar | [![GitHub](https://img.shields.io/badge/mkaspulanwar-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mkaspulanwar) |
| Andri Rahmadani | [![GitHub](https://img.shields.io/badge/AndriRahmadani12-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/AndriRahmadani12) |
| Henny Kartika | [![GitHub](https://img.shields.io/badge/hennykartika-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hennykartika) |

## Teknologi Utama

| Package             | Fungsi                |
| ------------------- | --------------------- |
| `fastapi`           | Framework API         |
| `uvicorn[standard]` | ASGI server           |
| `pydantic`          | Validasi schema       |
| `pydantic-settings` | Config `.env`         |
| `sqlalchemy`        | ORM database          |
| `alembic`           | Migration database    |
| `psycopg2-binary`   | Driver PostgreSQL     |
| `openai`            | API LLM               |
| `python-multipart`  | Upload file audio     |
| `httpx`             | Async HTTP request    |
| `aiofiles`          | Async file handling   |
| `python-dotenv`     | Load env              |
| `whisper`           | Speech-to-text        |
| `torch`             | Dependency Whisper    |
| `torchaudio`        | Audio processing      |
| `ffmpeg-python`     | Convert/process audio |
| `redis`             | Queue/cache           |
| `celery`            | Background worker     |
| `tiktoken`          | Hitung token          |
| `numpy/pandas`      | Processing data       |

## Struktur Folder

```
meet-summarizer/
├── main.py                   # Entry point aplikasi FastAPI
├── requirements.txt          # Daftar dependensi Python
├── Dockerfile               # Konfigurasi container Docker
├── .env                     # Variabel environment (tidak di-commit)
├── .env.example             # Contoh file environment
├── .gitignore               # File yang diabaikan Git
├── migration/               # Folder migrasi database (Alembic)
│   └── ...
└── src/                     # Source code utama
    ├── core/                # Konfigurasi inti aplikasi
    │   ├── config/          # Pengaturan & konfigurasi (.env, settings)
    │   │   └── settiing.py
    │   ├── database/        # Koneksi & setup database
    │   ├── logging/         # Konfigurasi logging
    │   │   └── logger.py
    │   └── storage/         # Penyimpanan file (local/cloud)
    │
    ├── models/              # SQLAlchemy ORM models
    │   └── __init__.py
    │
    ├── prompts/             # Template prompt untuk LLM
    │
    ├── repositories/        # Database access layer (CRUD operations)
    │
    ├── router/              # API endpoints (FastAPI routers)
    │   └── upload.py        # Endpoint upload file audio
    │
    ├── schemas/             # Pydantic models (request/response validation)
    │
    ├── services/            # Business logic utama
    │   ├── model_loader/    # Load AI/ML models (Whisper, dll)
    │   ├── pdf_generator/   # Generate dokumen PDF
    │   ├── pdf_templates/   # Template PDF
    │   │   ├── template_a/  # Template A (struktur ringkasan tipe A)
    │   │   ├── template_b/  # Template B (struktur ringkasan tipe B)
    │   │   └── template_c/  # Template C (struktur ringkasan tipe C)
    │   ├── pipeline/        # Orchestrasi alur kerja (transcribe → summarize → PDF)
    │   ├── summary_generator/  # Generate ringkasan menggunakan LLM
    │   └── transcriber/     # Speech-to-text (Whisper integration)
    │
    ├── utils/               # Helper functions & utilities
    │
    └── worker/              # Celery background workers
        └── __init__.py      # Task queue untuk proses async
```

## Penjelasan Folder

### `src/core/`
Berisi konfigurasi fundamental aplikasi yang dipakai di seluruh project:
- **config/**: Pengaturan aplikasi dari environment variables
- **database/**: Setup koneksi database dan session management
- **logging/**: Konfigurasi format dan level logging
- **storage/**: Abstraksi untuk penyimpanan file (lokal, S3, dll)

### `src/models/`
Definisi tabel database menggunakan SQLAlchemy ORM. Setiap file merepresentasikan satu tabel/entitas.

### `src/prompts/`
Template teks yang digunakan untuk instruct LLM (OpenAI) dalam menghasilkan ringkasan dengan format tertentu.

### `src/repositories/`
Lapisan abstraksi untuk akses database. Memisahkan logika query dari business logic.

### `src/router/`
Definisi endpoint API FastAPI. Setiap file adalah grup endpoint terkait (upload, meetings, summaries, dll).

### `src/schemas/`
Validasi data menggunakan Pydantic. Mendefinisikan struktur request body dan response.

### `src/services/`
Business logic utama aplikasi

### `src/utils/`
Fungsi-fungsi pembantu yang reusable

### `src/worker/`
Background task menggunakan Celery untuk proses yang memakan waktu (transkripsi audio panjang, generate PDF).

### `migration/`
File migrasi database Alembic untuk versioning schema database.

## Alur Kerja Aplikasi

1. **Upload Audio** → File diterima via `router/upload.py`
2. **Queue Task** → Celery worker (`worker/`) memproses secara async
3. **Transcribe** → `transcriber/` mengubah audio jadi teks dengan Whisper
4. **Summarize** → `summary_generator/` kirim teks ke LLM untuk diringkas
5. **Generate PDF** → `pdf_generator/` dengan template yang dipilih
6. **Store Result** → PDF disimpan ke `storage/` dan metadata ke `models/`

## Cara Menjalankan

```bash
# Install dependensi
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env sesuai konfigurasi Anda

# Jalankan migrasi database
alembic upgrade head

# Jalankan server
uvicorn main:app --reload
```
