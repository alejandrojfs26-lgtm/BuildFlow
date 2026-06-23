import csv
from datetime import date
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import Client
from app.models.daily_report import DailyReport
from app.models.material import Material
from app.models.project import Project
from app.models.worker import Worker

EXPORT_DIR = Path(settings.storage_local_path) / "exports"


def _ensure_dir() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _entity_name(entity_type: str) -> str:
    names = {
        "projects": "Projects",
        "workers": "Workers",
        "clients": "Clients",
        "daily_reports": "Daily Reports",
        "materials": "Materials",
    }
    return names.get(entity_type, entity_type)


def generate_csv(entity_type: str, tenant_id: UUID, db: Session) -> str:
    _ensure_dir()
    filename = f"{entity_type}_{date.today().isoformat()}_{UUID.uuid4().hex[:8]}.csv"
    path = EXPORT_DIR / filename

    rows = _fetch_rows(entity_type, tenant_id, db)
    if not rows:
        path.write_text("")
        return str(path)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return str(path)


def generate_xlsx(entity_type: str, tenant_id: UUID, db: Session) -> str:
    try:
        from openpyxl import Workbook
    except ImportError:
        return generate_csv(entity_type, tenant_id, db)

    _ensure_dir()
    filename = f"{entity_type}_{date.today().isoformat()}_{UUID.uuid4().hex[:8]}.xlsx"
    path = EXPORT_DIR / filename

    rows = _fetch_rows(entity_type, tenant_id, db)
    wb = Workbook()
    ws = wb.active
    ws.title = _entity_name(entity_type)

    if rows:
        ws.append(list(rows[0].keys()))
        for row in rows:
            ws.append(list(row.values()))

    wb.save(str(path))
    return str(path)


def _fetch_rows(entity_type: str, tenant_id: UUID, db: Session) -> list[dict]:
    if entity_type == "projects":
        objs = db.query(Project).filter(Project.tenant_id == tenant_id).all()
        return [
            {
                "name": p.name,
                "code": p.code,
                "status": p.status,
                "budget": float(p.budget or 0),
                "start_date": p.start_date.isoformat() if p.start_date else "",
                "end_date": p.end_date.isoformat() if p.end_date else "",
            }
            for p in objs
        ]

    if entity_type == "workers":
        objs = db.query(Worker).filter(Worker.tenant_id == tenant_id).all()
        return [
            {
                "full_name": w.full_name,
                "dni": w.dni,
                "phone": w.phone or "",
                "email": w.email or "",
                "position": w.position or "",
                "specialty": w.specialty or "",
                "hourly_rate": w.hourly_rate or 0,
                "is_active": "Yes" if w.is_active else "No",
            }
            for w in objs
        ]

    if entity_type == "clients":
        objs = db.query(Client).filter(Client.tenant_id == tenant_id).all()
        return [
            {
                "name": c.name,
                "tax_id": c.tax_id or "",
                "email": c.email or "",
                "phone": c.phone or "",
                "is_company": "Yes" if c.is_company else "No",
                "contact_person": c.contact_person or "",
            }
            for c in objs
        ]

    if entity_type == "daily_reports":
        objs = (
            db.query(DailyReport)
            .filter(DailyReport.tenant_id == tenant_id)
            .all()
        )
        return [
            {
                "date": r.date.isoformat(),
                "project_id": str(r.project_id),
                "worker_id": str(r.worker_id),
                "hours_worked": r.hours_worked,
                "overtime": r.overtime_hours or 0,
                "status": r.status,
            }
            for r in objs
        ]

    if entity_type == "materials":
        objs = (
            db.query(Material)
            .filter(Material.tenant_id == tenant_id)
            .all()
        )
        return [
            {
                "name": m.name,
                "category": m.category or "",
                "unit": m.unit,
                "unit_price": m.unit_price or 0,
                "stock": m.stock or 0,
                "min_stock": m.min_stock or 0,
            }
            for m in objs
        ]

    return []
