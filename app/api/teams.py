from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.modules.models import Team, TeamMember, User
from app.schemas import TeamCreate, TeamOut, TeamMemberCreate
from app.api.common import ensure_user

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
async def list_teams(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return (await db.scalars(select(Team).where(Team.organization_id == user.organization_id).order_by(Team.name))).all()


@router.post("", response_model=TeamOut, status_code=201)
async def create_team(payload: TeamCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles("admin", "manager"))):
    obj = Team(organization_id=admin.organization_id, **payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.post("/{team_id}/members", status_code=204)
async def add_member(team_id: str, payload: TeamMemberCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles("admin", "manager"))):
    team = await db.scalar(select(Team).where(Team.id == team_id, Team.organization_id == admin.organization_id))
    if not team:
        raise HTTPException(404, "Team not found")
    await ensure_user(db, admin.organization_id, payload.user_id)
    existing = await db.scalar(select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == payload.user_id))
    if not existing:
        db.add(TeamMember(team_id=team.id, user_id=payload.user_id))
        await db.commit()
