from pydantic import BaseModel


class ProjectSummary(BaseModel):
    total: int
    planning: int
    in_progress: int
    completed: int
    cancelled: int


class WorkerSummary(BaseModel):
    total: int
    active: int


class ReportSummary(BaseModel):
    today: int
    pending_approval: int


class MaterialSummary(BaseModel):
    low_stock: int
    total_categories: int


class KpiData(BaseModel):
    project_completion_rate: float
    budget_utilization: float
    report_submission_rate: float
    avg_hours_per_worker: float
    total_material_cost: float
    active_assignments: int


class DashboardResponse(BaseModel):
    projects: ProjectSummary
    workers: WorkerSummary
    daily_reports: ReportSummary
    materials: MaterialSummary
    clients: int
    kpis: KpiData
