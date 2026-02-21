import logging
import structlog
import sys
import os
from typing import Any, Dict, Optional

def setup_structured_logging():
    """
    Configure strict JSON structured logging for ARTCI/CIMA compliance.
    Replaces standard library logging format with structlog JSON output.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = logging.INFO if environment == "production" else logging.DEBUG

    # If it's pure development environment, maybe print pretty logs. 
    # But to enforce ARTCI compliance structure universally, we default to JSON rendering.
    renderer = structlog.processors.JSONRenderer()
    if environment == "development":
        try:
            # Attempt to use pretty rendering for local DEV only
            # Needs 'colorama' package
            renderer = structlog.dev.ConsoleRenderer()
        except Exception:
            pass

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Add strict ARTCI keys
            _add_artci_compliance_keys,
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Silence chatty loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def _add_artci_compliance_keys(logger: logging.Logger, log_method: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Inject mandatory ARTCI logging dimensions to all logs"""
    event_dict["data_residency"] = "ci"
    return event_dict
