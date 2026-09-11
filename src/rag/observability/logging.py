import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):

    STANDARD_FIELDS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
    }

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        log_data = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        # Add fields passed through extra={...}
        for key, value in record.__dict__.items():

            if key not in self.STANDARD_FIELDS:
                log_data[key] = value

        # logger.exception(...) puts the traceback here
        if record.exc_info:
            log_data["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            log_data,
            default=str,
        )


def configure_logging() -> None:

    rag_logger = logging.getLogger("rag")

    rag_logger.setLevel(
        logging.INFO
    )

    handler = logging.StreamHandler()

    handler.setFormatter(
        JsonFormatter()
    )

    # Avoid duplicate handlers
    rag_logger.handlers.clear()

    rag_logger.addHandler(
        handler
    )

    # Don't send the same record to the root logger
    rag_logger.propagate = False