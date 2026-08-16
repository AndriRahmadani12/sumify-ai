from celery import Celery

from src.core.config.setting import settings

calery_app = Celery(
    "sumify_ai",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["src.worker.calery_task"],
)

# Queue names
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

    task_routes={
        "sumify_ai.tasks.transcribe_audio": {"queue": TRANSCRIBE_QUEUE},
        "sumify_ai.tasks.generate_summary": {"queue": SUMMARY_QUEUE},
        "sumify_ai.tasks.generate_pdf": {"queue": PDF_GENERATION_QUEUE},
    },

    result_expires=3600 * 24,
    result_extended=True,

    task_annotations={
        "sumify_ai.tasks.transcribe_audio": {"rate_limit": "10/s"},
        "sumify_ai.tasks.generate_summary": {"rate_limit": "10/s"},
        "sumify_ai.tasks.generate_pdf": {"rate_limit": "10/s"},
    },

    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,

    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 3600,
    }
)

calery_app.conf.task_queues = {
    TRANSCRIBE_QUEUE: {
        "exchange": "sumify_ai",
        "routing_key": "transcribe",
    },
    SUMMARY_QUEUE: {
        "exchange": "sumify_ai",
        "routing_key": "summary",
    },
    PDF_GENERATION_QUEUE: {
        "exchange": "sumify_ai",
        "routing_key": "pdf_generation",
    },
    "default": {
        "exchange": "sumify_ai",
        "routing_key": "default",
    },
}


def init_calery() -> Celery:
    return calery_app
