from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import Transfer, User, Customer, Lead, ServiceCase
from app.schemas import TransferCreate, TransferOut
from app.api.common import ensure_user, ensure_team

router = APIRouter(prefix="/transfers", tags=["team transfers"])


@router.post("", response_model=TransferOut, status_code=201)
async def transfer_entity(payload: TransferCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await ensure_user(db, user.organization_id, payload.to_user_id)
    await ensure_team(db, user.organization_id, payload.to_team_id)

    if payload.entity_type == "customer":
        obj = await db.scalar(select(Customer).where(Customer.id == payload.entity_id, Customer.organization_id == user.organization_id))
        if not obj:
            raise HTTPException(404, "Customer not found")
        customer_id = obj.id
        from_user_id, from_team_id = obj.relationship_owner_id, obj.relationship_team_id
        obj.relationship_owner_id = payload.to_user_id
        obj.relationship_team_id = payload.to_team_id
    elif payload.entity_type == "lead":
        obj = await db.scalar(select(Lead).where(Lead.id == payload.entity_id, Lead.organization_id == user.organization_id))
        if not obj:
            raise HTTPException(404, "Lead not found")
        customer_id = obj.customer_id
        from_user_id, from_team_id = obj.owner_id, obj.team_id
        obj.owner_id, obj.team_id = payload.to_user_id, payload.to_team_id
    else:
        obj = await db.scalar(select(ServiceCase).where(ServiceCase.id == payload.entity_id, ServiceCase.organization_id == user.organization_id))
        if not obj:
            raise HTTPException(404, "Case not found")
        customer_id = obj.customer_id
        from_user_id, from_team_id = obj.owner_id, obj.team_id
        obj.owner_id, obj.team_id = payload.to_user_id, payload.to_team_id

    transfer = Transfer(
        organization_id=user.organization_id, customer_id=customer_id,
        entity_type=payload.entity_type, entity_id=payload.entity_id,
        from_team_id=from_team_id, to_team_id=payload.to_team_id,
        from_user_id=from_user_id, to_user_id=payload.to_user_id,
        requested_by_id=user.id, reason=payload.reason,
    )
    db.add(transfer)
    await db.flush()
    from app.core.audit import record_audit
    record_audit(db, user, f"{payload.entity_type}.transferred", payload.entity_type, payload.entity_id,
                 {"to_team_id": str(payload.to_team_id) if payload.to_team_id else None,
                  "to_user_id": str(payload.to_user_id) if payload.to_user_id else None,
                  "reason": payload.reason})
    await db.commit()
    await db.refresh(transfer)
    return transfer


@router.get("", response_model=list[TransferOut])
async def list_transfers(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return (await db.scalars(select(Transfer).where(Transfer.organization_id == user.organization_id).order_by(Transfer.created_at.desc()).limit(200))).all()
