from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import Interaction, User
from app.schemas import InteractionCreate, InteractionOut
from app.api.common import ensure_customer, ensure_lead, ensure_case

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("", response_model=InteractionOut, status_code=201)
async def create_interaction(payload: InteractionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await ensure_customer(db, user.organization_id, payload.customer_id)
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
        raise HTTPException(422, "An interaction can be linked to a lead or a case, not both")
    data = payload.model_dump(exclude={"occurred_at"})
    obj = Interaction(organization_id=user.organization_id, created_by_id=user.id, occurred_at=payload.occurred_at or datetime.now(timezone.utc), **data)
    db.add(obj)
    await db.flush()
    from app.core.audit import record_audit
    record_audit(db, user, "interaction.created", "interaction", obj.id, {"channel": payload.channel.value})
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("", response_model=list[InteractionOut])
async def list_interactions(customer_id: UUID | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Interaction).where(Interaction.organization_id == user.organization_id)
    if customer_id:
        stmt = stmt.where(Interaction.customer_id == customer_id)
    return (await db.scalars(stmt.order_by(Interaction.occurred_at.desc()).limit(200))).all()
