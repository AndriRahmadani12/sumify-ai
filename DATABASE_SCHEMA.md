# Meeting Summarizer — Database & Migration

Skema DB + initial migration (Alembic) untuk bagian Henny.

## Struktur
```
meeting_summarizer/
├── app/
│   ├── database.py   # engine, session, Base
│   └── models.py     # 6 tabel: users, meetings, transcriptions, summaries, processing_jobs, pdf_templates
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
└── alembic.ini
```

## Cara pakai

1. Install dependency:
   ```
   pip install "sqlalchemy>=2.0" alembic "psycopg[binary]"
   ```

2. Set koneksi DB (sesuaikan user/password/host):
   ```
   export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/meeting_summarizer"
   ```

3. Jalankan migrasi:
   ```
   alembic upgrade head
   ```

4. Rollback kalau perlu:
   ```
   alembic downgrade -1
   ```

## Catatan
- Field di tabel `users` (auth) dan struktur JSON (`segments`, `key_points`, dll)
  masih asumsi dari diagram — konfirmasi dulu ke Ndri (yang pegang repositories/query)
  sebelum dianggap final.
- Setelah model berubah, generate migrasi baru dengan:
  `alembic revision --autogenerate -m "deskripsi perubahan"`
