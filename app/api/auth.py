from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.modules.models import Organization, User, UserRole
from app.schemas import RegisterOrganization, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register-organization", response_model=UserOut, status_code=201)
async def register_organization(payload: RegisterOrganization, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(409, "Email is already registered")
    org = Organization(name=payload.organization_name, timezone=payload.timezone)
    db.add(org)
    await db.flush()
    user = User(
        organization_id=org.id, full_name=payload.full_name, email=payload.email,
        password_hash=hash_password(payload.password), role=UserRole.admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == form.username, User.is_active.is_(True)))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
