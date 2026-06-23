import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import (
    http_request_duration_seconds,
    http_requests_in_flight,
    http_requests_total,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/metrics", "/health", "/ready"):
            return await call_next(request)

        method = request.method
        http_requests_in_flight.labels(method=method).inc()
        start = time.monotonic()

        response = None
        try:
            response = await call_next(request)
            return response
        except BaseException:
            response = None
            raise
        finally:
            duration = time.monotonic() - start
            status_code = response.status_code if response is not None else 500
            endpoint = request.url.path
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).observe(duration)
            http_requests_in_flight.labels(method=method).dec()
