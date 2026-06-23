from fastapi import APIRouter

from app.api.v1.endpoints import (
    assignments,
    auth,
    clients,
    daily_reports,
    dashboard,
    documents,
    exports,
    materials,
    photos,
    project_materials,
    projects,
    reports,
    tenants,
    workers,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
v1_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
v1_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
v1_router.include_router(workers.router, prefix="/workers", tags=["Workers"])
v1_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
v1_router.include_router(daily_reports.router, prefix="/daily-reports", tags=["Daily Reports"])
v1_router.include_router(photos.router, prefix="/photos", tags=["Photos"])
v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
v1_router.include_router(materials.router, prefix="/materials", tags=["Materials"])
v1_router.include_router(
    project_materials.router,
    prefix="/project-materials",
    tags=["Project Materials"],
)
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
v1_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
