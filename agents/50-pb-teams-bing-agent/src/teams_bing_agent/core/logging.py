from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


_RESERVED_LOG_RECORD_KEYS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


def _coerce_json_value(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
        }

        extras = {
            key: _coerce_json_value(value)
            for key, value in record.__dict__.items()
            if key not in _RESERVED_LOG_RECORD_KEYS and key not in {"trace_id", "span_id"}
        }
        if extras:
            payload["extra"] = extras

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Minimal structured logger (message + key=value pairs)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
