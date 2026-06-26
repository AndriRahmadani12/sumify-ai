# Catatan dari Henny — bagian Database

Guys, bagian DB udah. Jadi sementara nggak usah ada yang nyentuh folder
`models` sama `repositories` ya, biar nggak tabrakan pas merge.

## Yang udah jalan

Model ORM-nya (User, Meeting, Transcription, Summary, ProcessingJob, PDFTemplate)
plus fungsi CRUD-nya udah kelar. Aku nggak cuma nulis terus ngaku jalan — udah aku tes
pakai `scripts/smoke_test_crud.py`, dan create/read/update/delete/list-nya lolos semua.
Kalau mau cek sendiri tinggal jalanin skrip itu.

File yang aku tambah/ubah:

- `src/models/__init__.py` — model ORM-nya di sini
- `src/repositories/` — fungsi CRUD per tabel (base + per entitas)
- `src/core/database/postgree.py` — koneksi DB async (tadinya kosong)
- `src/core/config/setting.py` — aku benerin, baca catatan di bawah
- `requirements.txt` + `.env.example` — nambah config DB

## Cara pakainya

```python
from src.core.database.postgree import async_session_maker
from src.repositories import MeetingRepository
from src.schemas.common import ProcessingStatus

async with async_session_maker() as session:
    repo = MeetingRepository(session)
    meeting = await repo.create(user_id=1, title="Rapat Q1", language="id")
    await repo.update_status(meeting.id, ProcessingStatus.TRANSCRIBING)
```

## Beberapa keputusan yang aku ambil

Buat ID aku pakai **integer**, bukan UUID. Kemarin kan sempet bilang bebas — nah aku
pilih integer soalnya kode worker sama storage kalian udah terlanjur pakai
`meeting_id: int` dan `user_id: int`. Kalau aku maksa UUID, malah kerjaan kalian yang
harus dirombak. Jadi mending ngikut yang udah ada.

Terus satu meeting = satu transkrip = satu ringkasan (1:1), sesuai yang kemarin
disepakatin. `key_points`, `action_items`, sama `segments` aku simpen sebagai JSON dulu.
Kalau nanti ternyata perlu di-query satuan, baru kita pecah jadi tabel sendiri.

## Ada yang aku benerin di file config (sori sekalian)

Pas ngerjain ini aku nemu `setting.py`-nya error: `List` belum di-import jadi filenya
nggak bisa jalan, terus setelan `env_file`-nya juga salah jadi `.env` nggak kebaca.
Aku benerin sekalian, plus nambahin `DATABASE_URL` karena emang belum ada sama sekali.
Yang punya file monggo dicek kalau mau.

## Soal "uji coba langsung" yang kemarin

Ini yang penting. Yang nungguin tes end-to-end (upload sampai jadi PDF) — sabar dulu,
belum bisa jalan full, tapi bukan gara-gara DB. Bagianku udah siap. Yang masih nyangkut:

- `calery_task.py` — isi task transcribe & PDF masih `# TODO`, belum diisi
- `calery_app.py` — masih error, manggil `settings.CELERY_BROKER_URL` padahal di config
  namanya `broker_url`
- `main.py` — router-nya masih di-comment semua, jadi belum ada endpoint yang nyala

Jadi kalau dites sekarang, error-nya bakal di situ, bukan di CRUD-ku. Begitu task worker
keisi (transcribe bagianku, PDF bagian Kaspul) dan router-nya di-include, baru bisa
dites dari ujung ke ujung.

Kalau ada yang bingung sama kodenya colek aku aja.
