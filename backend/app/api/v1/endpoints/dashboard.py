from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(get_current_user),
):
    service = DashboardService(db)
    return service.get_dashboard(tenant_id)
