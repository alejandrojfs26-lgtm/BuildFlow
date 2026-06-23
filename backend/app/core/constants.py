from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    WORKER = "worker"
    CLIENT_VIEWER = "client_viewer"


class Permission(StrEnum):
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    CLIENT_CREATE = "client:create"
    CLIENT_READ = "client:read"
    CLIENT_UPDATE = "client:update"
    CLIENT_DELETE = "client:delete"
    WORKER_CREATE = "worker:create"
    WORKER_READ = "worker:read"
    WORKER_UPDATE = "worker:update"
    WORKER_DELETE = "worker:delete"
    DAILY_REPORT_CREATE = "daily_report:create"
    DAILY_REPORT_READ = "daily_report:read"
    DAILY_REPORT_UPDATE = "daily_report:update"
    DAILY_REPORT_APPROVE = "daily_report:approve"
    MATERIAL_CREATE = "material:create"
    MATERIAL_READ = "material:read"
    MATERIAL_UPDATE = "material:update"
    MATERIAL_DELETE = "material:delete"
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_DOWNLOAD = "report:download"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_DELETE = "document:delete"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),
    Role.ADMIN: {
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.CLIENT_CREATE,
        Permission.CLIENT_READ,
        Permission.CLIENT_UPDATE,
        Permission.CLIENT_DELETE,
        Permission.WORKER_CREATE,
        Permission.WORKER_READ,
        Permission.WORKER_UPDATE,
        Permission.WORKER_DELETE,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.DAILY_REPORT_APPROVE,
        Permission.MATERIAL_CREATE,
        Permission.MATERIAL_READ,
        Permission.MATERIAL_UPDATE,
        Permission.MATERIAL_DELETE,
        Permission.REPORT_CREATE,
        Permission.REPORT_READ,
        Permission.REPORT_DOWNLOAD,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
    },
    Role.PROJECT_MANAGER: {
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.CLIENT_READ,
        Permission.WORKER_READ,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.DAILY_REPORT_APPROVE,
        Permission.MATERIAL_READ,
        Permission.REPORT_CREATE,
        Permission.REPORT_READ,
        Permission.REPORT_DOWNLOAD,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_READ,
    },
    Role.WORKER: {
        Permission.PROJECT_READ,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.MATERIAL_READ,
    },
    Role.CLIENT_VIEWER: {
        Permission.PROJECT_READ,
        Permission.REPORT_READ,
        Permission.REPORT_DOWNLOAD,
        Permission.DOCUMENT_READ,
    },
}


class ProjectStatus(StrEnum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DailyReportStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class MaterialUnit(StrEnum):
    UNIT = "unit"
    KG = "kg"
    M2 = "m2"
    M3 = "m3"
    M = "m"
    HOUR = "hour"
    LITER = "liter"


class ReportType(StrEnum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    FINANCIAL = "financial"
    CUSTOM = "custom"


class ReportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
