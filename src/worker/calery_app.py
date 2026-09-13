from celery import Celery

from src.core.config.setting import settings

calery_app = Celery(
    "sumify_ai",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["src.worker.calery_task"],
)

# Nama queue. Harus sama dengan argumen queue= pada decorator di calery_task.py.
TRANSCRIBE_QUEUE = "transcription"
SUMMARY_QUEUE = "summarization"
PDF_GENERATION_QUEUE = "pdf_generation"

calery_app.conf.update(
    task_serializer=settings.task_serializer,
    accept_content=settings.accept_content,
    result_serializer=settings.result_serializer,
    timezone=settings.timezone,
    enable_utc=settings.enable_utc,
    task_track_started=settings.task_track_started,
    task_time_limit=settings.task_time_limit,
    worker_prefetch_multiplier=settings.worker_prefetch_multiplier,

    # Routing ditentukan lewat queue= di decorator masing-masing task,
    # jadi task_routes tidak dipakai. Sebelumnya blok itu menunjuk ke nama
    # task "sumify_ai.tasks.*" yang tidak pernah terdaftar, sehingga task
    # tidak sampai ke worker.
    task_default_queue="default",

    result_expires=3600 * 24,
    result_extended=True,

    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,

    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 3600,
    },
)


def init_calery() -> Celery:
    return calery_app