from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import ServiceCase, User, CaseStatus
from app.schemas import CaseCreate, CaseUpdate, CaseOut
from app.api.common import ensure_customer, ensure_user, ensure_team

router = APIRouter(prefix="/cases", tags=["service cases"])


@router.get("", response_model=list[CaseOut])
async def list_cases(status: CaseStatus | None = None, customer_id: UUID | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(ServiceCase).where(ServiceCase.organization_id == user.organization_id)
    if status:
        stmt = stmt.where(ServiceCase.status == status)
    if customer_id:
        stmt = stmt.where(ServiceCase.customer_id == customer_id)
    return (await db.scalars(stmt.order_by(ServiceCase.updated_at.desc()).limit(200))).all()


@router.post("", response_model=CaseOut, status_code=201)
async def create_case(payload: CaseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await ensure_customer(db, user.organization_id, payload.customer_id)
    await ensure_user(db, user.organization_id, payload.owner_id)
    await ensure_team(db, user.organization_id, payload.team_id)
    obj = ServiceCase(organization_id=user.organization_id, **payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await db.scalar(select(ServiceCase).where(ServiceCase.id == case_id, ServiceCase.organization_id == user.organization_id))
    if not obj:
        raise HTTPException(404, "Case not found")
    return obj


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case(case_id: UUID, payload: CaseUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await get_case(case_id, db, user)
    data = payload.model_dump(exclude_unset=True)
    await ensure_user(db, user.organization_id, data.get("owner_id"))
    await ensure_team(db, user.organization_id, data.get("team_id"))
    if data.get("status") == CaseStatus.resolved and not data.get("resolution", obj.resolution):
        raise HTTPException(422, "Resolution details are required")
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj
