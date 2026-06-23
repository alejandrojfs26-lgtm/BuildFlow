FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install runtime dependencies only (no editable install)
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi[standard] uvicorn[standard] \
    sqlalchemy alembic psycopg2-binary \
    redis celery[redis] \
    pydantic pydantic-settings \
    python-jose[cryptography] passlib[bcrypt] \
    python-multipart structlog \
    fpdf2 openpyxl


FROM python:3.13-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only what's needed at runtime
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY start.sh .
COPY Procfile .
COPY railway.toml .

EXPOSE 8000

RUN chmod +x start.sh

CMD ["bash", "start.sh"]
