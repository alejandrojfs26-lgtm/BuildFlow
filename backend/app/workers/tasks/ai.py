"""AI/ML analysis tasks — forecasting, anomaly detection, usage trends.

Architecture:
  - Each task reads historical data from DB, runs analysis, stores results.
  - Analysis results are stored per-tenant (extensible to per-project).
  - Models are purely statistical (no external ML deps required).
  - `_ModelRegistry` is the extension point for scikit-learn/PyTorch models.

Triggered by:
  - Celery Beat (daily/weekly schedules)
  - Event hooks (e.g., after project status change)
  - Manual user request via API
"""

from collections.abc import Callable
from datetime import date, timedelta
from uuid import UUID

from app.workers.celery_app import celery_app
from app.workers.db import get_db

# ---------------------------------------------------------------------------
# Model registry — extension point for ML models
# ---------------------------------------------------------------------------

_ModelFn = Callable[..., dict]

_model_registry: dict[str, _ModelFn] = {}


def register_model(name: str) -> Callable[[_ModelFn], _ModelFn]:
    """Decorator to register a model for discovery and scheduling."""

    def wrapper(fn: _ModelFn) -> _ModelFn:
        _model_registry[name] = fn
        return fn

    return wrapper


def list_models() -> list[str]:
    return list(_model_registry)


# ---------------------------------------------------------------------------
# Analysis tasks
# ---------------------------------------------------------------------------


@celery_app.task(acks_late=True)
def analyze_tenant(tenant_id: str) -> dict:
    """Run all registered models for a tenant and store results.

    Called daily by Celery Beat.
    """
    results: dict[str, dict] = {}
    for name, model_fn in _model_registry.items():
        try:
            results[name] = model_fn(tenant_id=tenant_id)
        except Exception as exc:
            results[name] = {"error": str(exc)}

    _store_analysis_results(tenant_id, results)
    return results


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    acks_late=True,
)
def forecast_costs(self, tenant_id: str) -> dict:
    """Forecast project costs based on historical spending trends.

    Uses weighted moving average of material costs over the last N months.
    """

    with get_db() as db:
        from app.models.project_material import ProjectMaterial

        six_months_ago = date.today() - timedelta(days=180)
        rows = (
            db.query(ProjectMaterial)
            .filter(
                ProjectMaterial.tenant_id == UUID(tenant_id),
                ProjectMaterial.date >= six_months_ago,
            )
            .order_by(ProjectMaterial.date.asc())
            .all()
        )

        if len(rows) < 2:
            return {"status": "insufficient_data", "forecast": None}

        monthly_totals: dict[str, float] = {}
        for row in rows:
            month_key = row.date.strftime("%Y-%m")
            monthly_totals[month_key] = (
                monthly_totals.get(month_key, 0) + float(row.total_price)
            )

        sorted_months = sorted(monthly_totals.keys())
        values = [monthly_totals[m] for m in sorted_months]

        # Weighted moving average (more weight to recent months)
        weights = [i + 1 for i in range(len(values))]
        wma = sum(v * w for v, w in zip(values, weights)) / sum(weights)

        # Simple trend: linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den else 0.0

        forecast = {
            "weighted_moving_avg": round(wma, 2),
            "monthly_trend": round(slope, 2),
            "next_month_forecast": round(wma + slope, 2),
            "months_analyzed": n,
            "period": sorted_months,
        }

    _store_analysis_results(tenant_id, {"cost_forecast": forecast})
    return forecast


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    acks_late=True,
)
def detect_anomalies(self, tenant_id: str) -> dict:
    """Detect anomalous daily reports (unusual hours, overtime patterns).

    Flags reports where hours_worked deviates >2σ from the worker's mean.
    """
    import statistics


    with get_db() as db:
        from app.models.daily_report import DailyReport

        reports = (
            db.query(DailyReport)
            .filter(
                DailyReport.tenant_id == UUID(tenant_id),
                DailyReport.date >= date.today() - timedelta(days=90),
            )
            .all()
        )

        if len(reports) < 5:
            return {"status": "insufficient_data", "anomalies": []}

        hours = [float(r.hours_worked) for r in reports]
        mean = statistics.mean(hours)
        stdev = statistics.stdev(hours) if len(hours) > 1 else 0.0
        threshold = 2.0 * stdev if stdev > 0 else 3.0

        anomalies = [
            {
                "report_id": r.id.hex,
                "worker_id": r.worker_id.hex,
                "date": r.date.isoformat(),
                "hours_worked": float(r.hours_worked),
                "z_score": round((float(r.hours_worked) - mean) / stdev, 2)
                if stdev
                else 0.0,
                "reason": "high_hours" if r.hours_worked > mean + threshold else "low_hours",
            }
            for r in reports
            if abs(float(r.hours_worked) - mean) > threshold
        ]

        result = {
            "status": "completed",
            "anomalies_count": len(anomalies),
            "anomalies": anomalies[:50],
            "global_mean": round(mean, 2),
            "global_stdev": round(stdev, 2),
        }

    _store_analysis_results(tenant_id, {"anomalies": result})
    return result


@celery_app.task(acks_late=True)
def predict_material_usage(tenant_id: str) -> dict:
    """Predict future material needs based on consumption velocity."""

    with get_db() as db:
        from app.models.material import Material
        from app.models.project_material import ProjectMaterial

        materials = (
            db.query(Material)
            .filter(Material.tenant_id == UUID(tenant_id))
            .all()
        )

        if not materials:
            return {"status": "no_materials", "predictions": []}

        predictions = []
        ninety_days_ago = date.today() - timedelta(days=90)

        for mat in materials:
            usage = (
                db.query(ProjectMaterial)
                .filter(
                    ProjectMaterial.material_id == mat.id,
                    ProjectMaterial.tenant_id == UUID(tenant_id),
                    ProjectMaterial.date >= ninety_days_ago,
                )
                .all()
            )

            total_consumed = sum(float(u.quantity) for u in usage)
            daily_rate = total_consumed / 90.0 if usage else 0.0
            current_stock = float(mat.stock or 0)
            days_until_empty = (
                round(current_stock / daily_rate) if daily_rate > 0 else None
            )

            predictions.append({
                "material_id": mat.id.hex,
                "material_name": mat.name,
                "current_stock": current_stock,
                "daily_consumption_rate": round(daily_rate, 2),
                "days_until_depleted": days_until_empty,
                "restock_recommended": (
                    days_until_empty is not None and days_until_empty <= 30
                ),
            })

        result = {
            "status": "completed",
            "updated_at": date.today().isoformat(),
            "predictions": predictions,
        }

    _store_analysis_results(tenant_id, {"material_usage": result})
    return result


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


def _store_analysis_results(tenant_id: str, results: dict) -> None:
    """Persist analysis results for API consumption.

    Current: stores in Redis cache with TTL.
    Future: stores in a dedicated analytics_results table.
    """
    import json

    try:
        from app.utils.redis_client import redis_client

        key = f"analysis:{tenant_id}"
        existing = redis_client.get(key)
        base = json.loads(existing) if existing else {}
        base.update(results)
        redis_client.setex(key, 86400 * 7, json.dumps(base))
    except Exception:
        pass
