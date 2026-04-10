from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import Task, User, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.api.common import ensure_customer, ensure_user, ensure_lead, ensure_case

router = APIRouter(prefix="/tasks", tags=["tasks and reminders"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(status: TaskStatus | None = None, due_before: datetime | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Task).where(Task.organization_id == user.organization_id)
    if status:
        stmt = stmt.where(Task.status == status)
    if due_before:
        stmt = stmt.where(Task.due_at <= due_before)
    return (await db.scalars(stmt.order_by(Task.due_at).limit(200))).all()


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await ensure_customer(db, user.organization_id, payload.customer_id)
    await ensure_user(db, user.organization_id, payload.owner_id)
    await ensure_lead(db, user.organization_id, payload.lead_id)
    await ensure_case(db, user.organization_id, payload.case_id)
    if payload.lead_id:
        from app.modules.models import Lead
        lead = await db.scalar(select(Lead).where(Lead.id == payload.lead_id, Lead.organization_id == user.organization_id))
        if lead.customer_id != payload.customer_id:
            raise HTTPException(422, "Lead must belong to the selected customer")
    if payload.case_id:
        from app.modules.models import ServiceCase
        case = await db.scalar(select(ServiceCase).where(ServiceCase.id == payload.case_id, ServiceCase.organization_id == user.organization_id))
        if case.customer_id != payload.customer_id:
            raise HTTPException(422, "Case must belong to the selected customer")
    if payload.lead_id and payload.case_id:
        raise HTTPException(422, "A task can be associated with a lead or case, not both")
    obj = Task(organization_id=user.organization_id, **payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: UUID, payload: TaskUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await db.scalar(select(Task).where(Task.id == task_id, Task.organization_id == user.organization_id))
    if not obj:
        raise HTTPException(404, "Task not found")
    data = payload.model_dump(exclude_unset=True)
    await ensure_user(db, user.organization_id, data.get("owner_id"))
    for key, value in data.items():
        setattr(obj, key, value)
    if obj.status == TaskStatus.completed and obj.completed_at is None:
        obj.completed_at = datetime.now(timezone.utc)
    if obj.status != TaskStatus.completed:
        obj.completed_at = None
    await db.commit()
    await db.refresh(obj)
    return obj
