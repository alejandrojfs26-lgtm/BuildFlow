from prometheus_client import Counter, Gauge, Histogram, Info

info = Info("buildflow", "BuildFlow application metadata")
info.info({"version": "0.1.0", "app": "BuildFlow"})

http_requests_total = Counter(
    "buildflow_http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "buildflow_http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_flight = Gauge(
    "buildflow_http_requests_in_flight",
    "Current number of in-flight HTTP requests",
    labelnames=["method"],
)

db_connection_pool_size = Gauge(
    "buildflow_db_pool_size",
    "Database connection pool size",
    labelnames=["state"],
)

db_query_duration_seconds = Histogram(
    "buildflow_db_query_duration_seconds",
    "Database query duration in seconds",
    labelnames=["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

db_query_errors_total = Counter(
    "buildflow_db_query_errors_total",
    "Total database query errors",
    labelnames=["operation"],
)

auth_attempts_total = Counter(
    "buildflow_auth_attempts_total",
    "Total authentication attempts",
    labelnames=["method", "status"],
)

cache_hits_total = Counter(
    "buildflow_cache_hits_total",
    "Total cache hits",
    labelnames=["cache"],
)

cache_misses_total = Counter(
    "buildflow_cache_misses_total",
    "Total cache misses",
    labelnames=["cache"],
)

celery_tasks_total = Counter(
    "buildflow_celery_tasks_total",
    "Total Celery tasks executed",
    labelnames=["task", "status"],
)

celery_task_duration_seconds = Histogram(
    "buildflow_celery_task_duration_seconds",
    "Celery task duration in seconds",
    labelnames=["task"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

celery_queue_depth = Gauge(
    "buildflow_celery_queue_depth",
    "Current depth of Celery queues",
    labelnames=["queue"],
)

# Business metrics
projects_total = Gauge(
    "buildflow_projects_total",
    "Total projects",
    labelnames=["status"],
)

workers_total = Gauge(
    "buildflow_workers_total",
    "Total workers",
    labelnames=["is_active"],
)

daily_reports_total = Counter(
    "buildflow_daily_reports_total",
    "Total daily reports created",
    labelnames=["status"],
)

daily_reports_today = Gauge(
    "buildflow_daily_reports_today",
    "Daily reports created today",
)

active_tenants = Gauge(
    "buildflow_active_tenants_total",
    "Total active tenants",
)

low_stock_materials = Gauge(
    "buildflow_low_stock_materials_total",
    "Materials with stock below minimum",
)
