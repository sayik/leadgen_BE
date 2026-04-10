from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.models import User, Team, Customer, Lead, ServiceCase


async def ensure_user(db: AsyncSession, org_id: UUID, user_id: UUID | None):
    if user_id is None:
        return
    obj = await db.scalar(select(User).where(User.id == user_id, User.organization_id == org_id))
    if not obj:
        raise HTTPException(404, "Employee not found in this organization")


async def ensure_team(db: AsyncSession, org_id: UUID, team_id: UUID | None):
    if team_id is None:
        return
    obj = await db.scalar(select(Team).where(Team.id == team_id, Team.organization_id == org_id))
    if not obj:
        raise HTTPException(404, "Team not found in this organization")


async def ensure_customer(db: AsyncSession, org_id: UUID, customer_id: UUID):
    obj = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.organization_id == org_id))
    if not obj:
        raise HTTPException(404, "Customer not found")
    return obj


async def ensure_lead(db: AsyncSession, org_id: UUID, lead_id: UUID | None):
    if lead_id is None:
        return
    obj = await db.scalar(select(Lead).where(Lead.id == lead_id, Lead.organization_id == org_id))
    if not obj:
        raise HTTPException(404, "Lead not found")


async def ensure_case(db: AsyncSession, org_id: UUID, case_id: UUID | None):
    if case_id is None:
        return
    obj = await db.scalar(select(ServiceCase).where(ServiceCase.id == case_id, ServiceCase.organization_id == org_id))
    if not obj:
        raise HTTPException(404, "Case not found")
