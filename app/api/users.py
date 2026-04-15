from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.security import hash_password
from app.modules.models import User, UserRole
from app.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return (await db.scalars(select(User).where(User.organization_id == user.organization_id).order_by(User.full_name))).all()


@router.post("", response_model=UserOut, status_code=201)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(409, "Email already exists in organization")
    obj = User(
        organization_id=admin.organization_id, full_name=payload.full_name,
        email=payload.email, password_hash=hash_password(payload.password), role=payload.role
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
