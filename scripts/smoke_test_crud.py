"""Smoke test CRUD layer ke database asli (Postgres).

Jalankan untuk membuktikan lapisan DB benar-benar bekerja sebelum disambung ke
worker/router.

Cara pakai:
    1. Pastikan Postgres jalan & DATABASE_URL sudah di-set (.env atau env var), mis:
       export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/sumify"
    2. python scripts/smoke_test_crud.py

Catatan: skrip ini memanggil init_models() yang MEMBUAT tabel langsung dari metadata.
Pakai database kosong / khusus testing, bukan DB produksi.
"""
import asyncio
import os
import sys

# agar "src" bisa di-import saat skrip dijalankan langsung
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database.postgree import async_session_maker, init_models
from src.repositories import (
    MeetingRepository,
    ProcessingJobRepository,
    SummaryRepository,
    TranscriptionRepository,
    UserRepository,
)
from src.schemas.common import JobStatus, JobType, PaginationParams, ProcessingStatus


def ok(label: str) -> None:
    print(f"  \033[92m✓\033[0m {label}")


async def run() -> None:
    print("→ Membuat tabel (init_models)...")
    await init_models()

    async with async_session_maker() as session:
        users = UserRepository(session)
        meetings = MeetingRepository(session)
        trans = TranscriptionRepository(session)
        summaries = SummaryRepository(session)
        jobs = ProcessingJobRepository(session)

        print("\n[CREATE]")
        u = await users.create(email="smoke@test.com", password_hash="x", name="Smoke")
        ok(f"user dibuat (id={u.id})")
        m = await meetings.create(user_id=u.id, title="Rapat Uji", language="id")
        assert m.status == ProcessingStatus.UPLOADED
        ok(f"meeting dibuat (id={m.id}, status={m.status.value})")

        print("\n[READ]")
        assert (await meetings.get_by_id(m.id)).title == "Rapat Uji"
        assert (await users.get_by_email("smoke@test.com")).id == u.id
        ok("get_by_id & get_by_email")

        print("\n[UPDATE status]")
        m = await meetings.update_status(m.id, ProcessingStatus.TRANSCRIBING)
        assert m.status == ProcessingStatus.TRANSCRIBING
        ok(f"status -> {m.status.value}")

        print("\n[Relasi 1:1 + JSON]")
        await trans.create(meeting_id=m.id, full_text="halo",
                           segments=[{"start": 0.0, "end": 1.0, "text": "halo"}], language="id")
        await summaries.create(meeting_id=m.id, summary="ringkas",
                               key_points=["a", "b"], action_items=[], decisions=[])
        ok("transcription & summary tersimpan (JSON utuh)")

        print("\n[ProcessingJob]")
        j = await jobs.create(meeting_id=m.id, job_type=JobType.TRANSCRIPTION)
        j = await jobs.update_status(j.id, JobStatus.FAILURE, error="contoh error")
        assert j.status == JobStatus.FAILURE and j.error == "contoh error"
        ok("job dibuat & status diupdate (failure + error)")

        print("\n[Eager load relasi]")
        full = await meetings.get_with_relations(m.id)
        assert full.transcription and full.summary and len(full.jobs) == 1
        ok("get_with_relations memuat transcription, summary, jobs")

        print("\n[LIST + pagination + COUNT]")
        for i in range(3):
            await meetings.create(user_id=u.id, title=f"M{i}")
        items, total = await meetings.list(PaginationParams(page=1, page_size=10))
        ok(f"list -> total={total}, items={len(items)}")

        print("\n[DELETE + cascade]")
        assert await meetings.delete(m.id) is True
        assert await trans.get_by_meeting_id(m.id) is None
        ok("meeting terhapus + transcription ikut (cascade)")

        # Bersihkan sisa data uji
        for leftover in await meetings.get_by_user(u.id):
            await meetings.delete(leftover.id)
        await users.delete(u.id)

    print("\n\033[92mSEMUA CRUD LULUS ✓\033[0m")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as exc:  # noqa: BLE001
        print(f"\n\033[91mGAGAL:\033[0m {type(exc).__name__}: {exc}")
        sys.exit(1)
