from celery import Celery

from src.core.config.setting import settings

settings = Settings()

calery_app = Celery(
    "sumify_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # include=["src.worker.calery_task"]
)

# Queue names
TRANSCRIBE_QUEUE = "transcription"
SUMMARY_QUEUE = "summarization"
PDF_GENERATION_QUEUE = "pdf_generation"

calery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,

    task_routes={
        "sumify_ai.tasks.transcribe_audio": {"queue": "transcribe"},
        "sumify_ai.tasks.generate_summary": {"queue": "summary"},
        "sumify_ai.tasks.generate_pdf": {"queue": "pdf"},
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