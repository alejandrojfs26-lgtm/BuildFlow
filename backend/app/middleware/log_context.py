from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import trace_context


class LogContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/metrics", "/health", "/ready"):
            return await call_next(request)

        ctx = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }

        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            ctx["tenant_id"] = tenant_id

        token = trace_context.set(ctx)
        try:
            return await call_next(request)
        finally:
            trace_context.reset(token)
