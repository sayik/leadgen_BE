from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import Customer, Lead, ServiceCase, Task, LeadStatus, TaskStatus, CaseStatus, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    org = user.organization_id
    now = datetime.now(timezone.utc)
    customers = await db.scalar(select(func.count()).select_from(Customer).where(Customer.organization_id == org))
    new_leads = await db.scalar(select(func.count()).select_from(Lead).where(Lead.organization_id == org, Lead.status.in_([LeadStatus.new, LeadStatus.callback_required])))
    active_leads = await db.scalar(select(func.count()).select_from(Lead).where(Lead.organization_id == org, Lead.status.not_in([LeadStatus.won, LeadStatus.lost])))
    open_cases = await db.scalar(select(func.count()).select_from(ServiceCase).where(ServiceCase.organization_id == org, ServiceCase.status.not_in([CaseStatus.resolved, CaseStatus.closed])))
    overdue_tasks = await db.scalar(select(func.count()).select_from(Task).where(Task.organization_id == org, Task.status == TaskStatus.open, Task.due_at < now))
    my_tasks = await db.scalar(select(func.count()).select_from(Task).where(Task.organization_id == org, Task.owner_id == user.id, Task.status == TaskStatus.open))
    return {
        "customers": customers or 0,
        "new_or_callback_leads": new_leads or 0,
        "active_leads": active_leads or 0,
        "open_cases": open_cases or 0,
        "overdue_tasks": overdue_tasks or 0,
        "my_open_tasks": my_tasks or 0,
    }
