"""
Structured logging configuration for the Conference Talk Classifier.

This module provides a centralized logging configuration with support for
console and file logging, structured JSON output, and contextual information.
"""
import functools
import json
import logging
import logging.config
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

import structlog

# Type variable for decorator return type
F = TypeVar("F", bound=Callable[..., Any])


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
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
                "getMessage",
            }:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """Initialize context filter."""
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    include_console: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Set up structured logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_format: Whether to use JSON formatting
        include_console: Whether to include console output
        context: Additional context to include in all log messages

    Returns:
        Configured logger instance
    """
    # Create logs directory if logging to file
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog with proper processor types
    processors: list[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if json_format else structlog.dev.ConsoleRenderer(),
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {"()": JSONFormatter},
        },
        "filters": {
            "context": {"()": ContextFilter, "context": context or {}},
        },
        "handlers": {},
        "loggers": {
            "": {  # Root logger
                "level": level,
                "handlers": [],
                "propagate": False,
            },
            "classifier": {
                "level": level,
                "handlers": [],
                "propagate": False,
            },
        },
    }

    handlers = []

    # Console handler
    if include_console:
        console_handler = {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "json" if json_format else "standard",
            "filters": ["context"],
            "stream": "ext://sys.stdout",
        }
        logging_config["handlers"]["console"] = console_handler
        handlers.append("console")

    # File handler
    if log_file:
        file_handler = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "json" if json_format else "detailed",
            "filters": ["context"],
            "filename": str(log_file),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }
        logging_config["handlers"]["file"] = file_handler
        handlers.append("file")

    # Error file handler (always in detailed format)
    if log_file:
        error_file = log_file.parent / f"{log_file.stem}_errors.log"
        error_handler = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filters": ["context"],
            "filename": str(error_file),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 3,
            "encoding": "utf-8",
        }
        logging_config["handlers"]["error_file"] = error_handler
        handlers.append("error_file")

    # Assign handlers to loggers
    logging_config["loggers"][""]["handlers"] = handlers
    logging_config["loggers"]["classifier"]["handlers"] = handlers

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Return the main logger
    return logging.getLogger("classifier")


def get_logger(name: str = "classifier") -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name

    Returns:
        Configured structlog logger
    """
    # Type: ignore is needed here because structlog.get_logger returns Any
    # but we know it's actually a BoundLogger after configuration
    return structlog.get_logger(name)  # type: ignore[no-any-return]


class LogContext:
    """Context manager for adding temporary logging context."""

    def __init__(self, logger: structlog.stdlib.BoundLogger, **kwargs: Any):
        """Initialize log context."""
        self.logger = logger
        self.context = kwargs
        self.bound_logger: Optional[structlog.stdlib.BoundLogger] = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        """Enter context with additional fields."""
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context."""
        self.bound_logger = None


def log_performance(logger: structlog.stdlib.BoundLogger, operation: str) -> Callable[[F], F]:
    """Decorator for logging performance metrics."""
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Operation completed",
                    operation=operation,
                    duration_seconds=round(duration, 3),
                    function=func.__name__,
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Operation failed",
                    operation=operation,
                    duration_seconds=round(duration, 3),
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        return wrapper  # type: ignore

    return decorator


def configure_classifier_logging(
    log_level: Optional[str] = None,
    log_file: bool = True,
    json_format: bool = False,
) -> structlog.stdlib.BoundLogger:
    """
    Configure logging specifically for the classifier application.

    Args:
        log_level: Override logging level from environment
        log_file: Whether to enable file logging
        json_format: Whether to use JSON format

    Returns:
        Configured logger instance
    """
    # Determine log level from environment or default
    level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()

    # Set up log file path
    log_file_path = None
    if log_file:
        logs_dir = Path("logs")
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file_path = logs_dir / f"classifier_{timestamp}.log"

    # Add application context
    context = {
        "application": "conference-talk-classifier",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

    # Setup logging
    setup_logging(
        level=level,
        log_file=log_file_path,
        json_format=json_format,
        include_console=True,
        context=context,
    )

    return get_logger("classifier")


# Configure default logger on module import
logger = configure_classifier_logging() 