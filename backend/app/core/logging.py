"""Structured logging: every log line is a set of key/value pairs, printed as JSON.

Logs from our code, from libraries and from uvicorn all go through the same pipeline,
and each line written during a request carries that request's `request_id`.
"""

import logging
import sys
from typing import Literal

import structlog

LogFormat = Literal["json", "console"]


def configure_logging(level: str = "INFO", log_format: LogFormat = "json") -> None:
    # Steps applied to every log line, whether it came from structlog or plain `logging`
    shared: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # adds request_id
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    renderer: list[structlog.types.Processor] = (
        [structlog.processors.format_exc_info, structlog.processors.JSONRenderer()]
        if log_format == "json"
        # Coloured, human-friendly lines for reading in a terminal
        else [structlog.dev.ConsoleRenderer()]
    )

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, *renderer],
        )
    )
    handler._lumen = True  # type: ignore[attr-defined]

    root = logging.getLogger()
    # Replace only our own handler, so calling this twice (as tests do) never doubles lines
    # and handlers added by others (like pytest's log capture) stay in place
    for old in [h for h in root.handlers if getattr(h, "_lumen", False)]:
        root.removeHandler(old)
    root.addHandler(handler)
    root.setLevel(level)

    # Send uvicorn's own messages through the same pipeline, and switch off its access
    # log: RequestContextMiddleware writes a richer one
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True
    # The HTTP client logs every call it makes (moderation API included): too chatty for INFO
    logging.getLogger("httpx2").setLevel(logging.WARNING)


def get_request_id() -> str | None:
    """The id of the request being handled, or None outside a request."""
    return structlog.contextvars.get_contextvars().get("request_id")
