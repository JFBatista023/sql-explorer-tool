import json
import logging
import os
import socket
from datetime import datetime, timezone
from typing import Any

LOGGER_NAME = "sql_explorer_readonly"


class JsonLikeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(JsonLikeFormatter())

    logger.addHandler(handler)
    return logger


def actor_context() -> dict[str, Any]:
    return {
        "os_user": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "client_name": os.getenv("MCP_CLIENT_NAME", "unknown"),
        "client_version": os.getenv("MCP_CLIENT_VERSION", "unknown"),
    }


def log_event(logger: logging.Logger, level: int, message: str, **fields: Any) -> None:
    logger.log(level, message, extra={"extra_fields": fields})
