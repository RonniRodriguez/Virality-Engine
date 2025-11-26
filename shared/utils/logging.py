"""
Idea Inc - Logging Configuration

Structured logging with JSON output for production
and human-readable output for development.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor


def add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp to log events"""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(service_name: str) -> Processor:
    """Add service name to all log events"""
    def processor(
        logger: logging.Logger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        event_dict["service"] = service_name
        return event_dict
    return processor


def setup_logging(
    service_name: str = "ideainc",
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - "json" for production, "text" for development
    """
    # Shared processors for both formats
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_service_info(service_name),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if log_format == "json":
        # JSON format for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable format for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding temporary context to logs.
    
    Usage:
        with LogContext(request_id="abc123", user_id="user1"):
            logger.info("Processing request")
    """
    
    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self._token = None
    
    def __enter__(self) -> "LogContext":
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, *args: Any) -> None:
        if self._token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an HTTP request with standard fields.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
        extra: Optional extra fields
    """
    logger = get_logger("http")
    
    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if extra:
        log_data.update(extra)
    
    if status_code >= 500:
        logger.error("HTTP request", **log_data)
    elif status_code >= 400:
        logger.warning("HTTP request", **log_data)
    else:
        logger.info("HTTP request", **log_data)

