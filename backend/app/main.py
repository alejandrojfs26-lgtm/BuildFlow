import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import REGISTRY, generate_latest
from sqlalchemy.orm import Session

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.events import lifespan
from app.core.exceptions import AppError
from app.db.session import get_db
from app.middleware.log_context import LogContextMiddleware
from app.middleware.metrics import PrometheusMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.tenant import TenantMiddleware
from app.utils.health import HealthCheck

logger = structlog.get_logger("buildflow")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Tenant-ID",
    ],
)

app.add_middleware(PrometheusMiddleware)
app.add_middleware(LogContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TenantMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    logger.warning("app_error", code=exc.code, message=exc.message, status=exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


app.include_router(v1_router)


@app.get("/health", tags=["observability"])
async def liveness():
    return HealthCheck(None).liveness()


@app.get("/ready", tags=["observability"])
async def readiness(db: Session = Depends(get_db)):
    hc = HealthCheck(db)
    return hc.readiness(deep=True)


@app.get("/metrics", tags=["observability"])
async def metrics():
    return PlainTextResponse(
        generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
