import logging
import sys
from typing import Any

import structlog
from structlog.processors import JSONRenderer

from src.core.config.setting import settings


def configure_logging() -> None:
    shared_processors: list[structlog.types.Processor] = [
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Format positional arguments
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add caller info
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        # Filter by level
        structlog.stdlib.filter_by_level,
        # Render stack traces
        structlog.processors.format_exc_info,
        # Unicode decoder
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        # JSON formatting for production
        renderer: structlog.types.Processor = JSONRenderer()
    else:
        # Console formatting for development
        renderer = structlog.dev.ConsoleRenderer(
            colors=settings.is_development,
            pad_level=False,
        )

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str | None = None, **context: Any) -> structlog.stdlib.BoundLogger:
    logger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger
