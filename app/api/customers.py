from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import phonenumbers
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.models import Customer, Contact, ContactType, User
from app.schemas import CustomerCreate, CustomerUpdate, CustomerOut, ContactCreate, ContactOut
from app.api.common import ensure_user

router = APIRouter(prefix="/customers", tags=["customers"])


def normalize_contact(kind: ContactType, value: str, region: str = "IN") -> str:
    if kind == ContactType.phone:
        try:
            number = phonenumbers.parse(value, region)
            if not phonenumbers.is_valid_number(number):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException as exc:
            raise ValueError("Invalid phone number; use international format such as +919876543210") from exc
    if kind == ContactType.email:
        return value.strip().lower()
    return value.strip()


@router.get("", response_model=list[CustomerOut])
async def list_customers(
    q: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = select(Customer).where(Customer.organization_id == user.organization_id)
    if q:
        stmt = stmt.where(or_(Customer.name.ilike(f"%{q}%"), Customer.company_name.ilike(f"%{q}%"), Customer.email.ilike(f"%{q}%")))
    return (await db.scalars(stmt.order_by(Customer.updated_at.desc()).offset(offset).limit(limit))).all()


@router.post("", response_model=CustomerOut, status_code=201)
async def create_customer(payload: CustomerCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await ensure_user(db, user.organization_id, payload.relationship_owner_id)
    obj = Customer(organization_id=user.organization_id, **payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(customer_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.organization_id == user.organization_id))
    if not obj:
        raise HTTPException(404, "Customer not found")
    return obj


@router.patch("/{customer_id}", response_model=CustomerOut)
async def update_customer(customer_id: UUID, payload: CustomerUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.organization_id == user.organization_id))
    if not obj:
        raise HTTPException(404, "Customer not found")
    data = payload.model_dump(exclude_unset=True)
    await ensure_user(db, user.organization_id, data.get("relationship_owner_id"))
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.post("/{customer_id}/contacts", response_model=ContactOut, status_code=201)
async def add_contact(customer_id: UUID, payload: ContactCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    customer = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.organization_id == user.organization_id))
    if not customer:
        raise HTTPException(404, "Customer not found")
    try:
        normalized = normalize_contact(payload.contact_type, payload.value, payload.region)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    duplicate = await db.scalar(select(Contact).where(Contact.organization_id == user.organization_id, Contact.value_normalized == normalized))
    if duplicate:
        if duplicate.customer_id != customer_id:
            raise HTTPException(409, "This contact detail is already associated with another customer")
        raise HTTPException(409, "Contact detail already exists for this customer")
    data = payload.model_dump(exclude={"region"})
    obj = Contact(organization_id=user.organization_id, customer_id=customer_id, value=payload.value, value_normalized=normalized, **{k:v for k,v in data.items() if k != "value"})
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/{customer_id}/contacts", response_model=list[ContactOut])
async def list_contacts(customer_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await get_customer(customer_id, db, user)
    return (await db.scalars(select(Contact).where(Contact.customer_id == customer_id, Contact.organization_id == user.organization_id))).all()


@router.get("/{customer_id}/timeline")
async def customer_timeline(customer_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await get_customer(customer_id, db, user)
    from app.modules.models import Interaction, Task, Lead, ServiceCase
    interactions = (await db.scalars(select(Interaction).where(Interaction.customer_id == customer_id, Interaction.organization_id == user.organization_id).order_by(Interaction.occurred_at.desc()))).all()
    leads = (await db.scalars(select(Lead).where(Lead.customer_id == customer_id, Lead.organization_id == user.organization_id))).all()
    cases = (await db.scalars(select(ServiceCase).where(ServiceCase.customer_id == customer_id, ServiceCase.organization_id == user.organization_id))).all()
    tasks = (await db.scalars(select(Task).where(Task.customer_id == customer_id, Task.organization_id == user.organization_id).order_by(Task.due_at))).all()
    return {"interactions": interactions, "leads": leads, "cases": cases, "tasks": tasks}
