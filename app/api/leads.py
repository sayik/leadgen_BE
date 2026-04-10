from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import Lead, User, LeadStatus
from app.schemas import LeadCreate, LeadUpdate, LeadOut
from app.api.common import ensure_customer, ensure_user, ensure_team

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadOut])
async def list_leads(status: LeadStatus | None = None, customer_id: UUID | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Lead).where(Lead.organization_id == user.organization_id)
    if status:
        stmt = stmt.where(Lead.status == status)
    if customer_id:
        stmt = stmt.where(Lead.customer_id == customer_id)
    return (await db.scalars(stmt.order_by(Lead.updated_at.desc()).limit(200))).all()


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await ensure_customer(db, user.organization_id, payload.customer_id)
    await ensure_user(db, user.organization_id, payload.owner_id)
    await ensure_team(db, user.organization_id, payload.team_id)
    obj = Lead(organization_id=user.organization_id, **payload.model_dump())
    db.add(obj)
    await db.flush()
    from app.core.audit import record_audit
    record_audit(db, user, "lead.created", "lead", obj.id)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await db.scalar(select(Lead).where(Lead.id == lead_id, Lead.organization_id == user.organization_id))
    if not obj:
        raise HTTPException(404, "Lead not found")
    return obj


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: UUID, payload: LeadUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await get_lead(lead_id, db, user)
    data = payload.model_dump(exclude_unset=True)
    await ensure_user(db, user.organization_id, data.get("owner_id"))
    await ensure_team(db, user.organization_id, data.get("team_id"))
    if data.get("status") == LeadStatus.lost and not data.get("close_reason", obj.close_reason):
        raise HTTPException(422, "A reason is required when marking a lead as lost")
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj
