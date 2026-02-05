"""
Error Handlers for Policy Service
Sanitizes all exceptions to prevent information leakage.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

logger = logging.getLogger(__name__)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler that:
    - Logs full error details server-side
    - Returns generic message to client
    """
    # Log full error with traceback for debugging
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )
    
    # Generic response - no internal details exposed
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Request could not be processed"}
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions while sanitizing sensitive details.
    """
    # Log for monitoring
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} | Path: {request.url.path}"
    )
    
    # Safe status codes can pass through with their details
    safe_codes = {400, 401, 403, 404, 405, 409, 413, 422, 429}
    
    if exc.status_code in safe_codes:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    # For other codes (5xx), return generic message
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Request failed"}
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
