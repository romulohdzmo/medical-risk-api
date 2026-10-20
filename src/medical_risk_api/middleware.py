"""Structured logging and correlation middleware for clinical audit trails."""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
)
logger = logging.getLogger("clinical_api")


class ClinicalAuditMiddleware(BaseHTTPMiddleware):
    """Logs request metadata, latency, and assigns correlation IDs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time-MS"] = str(duration_ms)

        log_payload = (
            f'{{"correlation_id": "{correlation_id}", '
            f'"method": "{request.method}", '
            f'"path": "{request.url.path}", '
            f'"status_code": {response.status_code}, '
            f'"duration_ms": {duration_ms}}}'
        )
        logger.info(log_payload)

        return response
