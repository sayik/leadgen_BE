from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.modules.models import (
    UserRole, CustomerStatus, ContactType, InteractionChannel, InteractionDirection,
    LeadStatus, CaseStatus, TaskStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterOrganization(BaseModel):
    organization_name: str = Field(min_length=2, max_length=200)
    timezone: str = "Asia/Kolkata"
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=12)
    role: UserRole = UserRole.sales


class UserOut(ORMModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool


class TeamCreate(BaseModel):
    name: str
    description: str | None = None
    team_type: str = "general"


class TeamOut(ORMModel):
    id: UUID
    name: str
    description: str | None
    team_type: str


class TeamMemberCreate(BaseModel):
    user_id: UUID


class CustomerCreate(BaseModel):
    name: str
    company_name: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    location: str | None = None
    category: str | None = None
    source: str | None = None
    status: CustomerStatus = CustomerStatus.prospect
    relationship_owner_id: UUID | None = None
    notes: str | None = None
    custom_fields: dict = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    name: str | None = None
    company_name: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    location: str | None = None
    category: str | None = None
    source: str | None = None
    status: CustomerStatus | None = None
    relationship_owner_id: UUID | None = None
    notes: str | None = None
    custom_fields: dict | None = None


class CustomerOut(ORMModel):
    id: UUID
    name: str
    company_name: str | None
    email: str | None
    address: str | None
    location: str | None
    category: str | None
    source: str | None
    status: CustomerStatus
    relationship_owner_id: UUID | None
    notes: str | None
    custom_fields: dict
    created_at: datetime
    updated_at: datetime


class ContactCreate(BaseModel):
    contact_type: ContactType
    value: str
    label: str | None = None
    is_primary: bool = False
    is_verified: bool = False
    region: str = "IN"


class ContactOut(ORMModel):
    id: UUID
    customer_id: UUID
    contact_type: ContactType
    value: str
    value_normalized: str
    label: str | None
    is_primary: bool
    is_verified: bool


class InteractionCreate(BaseModel):
    customer_id: UUID
    lead_id: UUID | None = None
    case_id: UUID | None = None
    channel: InteractionChannel
    direction: InteractionDirection = InteractionDirection.outbound
    occurred_at: datetime | None = None
    summary: str = Field(min_length=2)
    outcome: str | None = None
    customer_interest: str | None = None
    next_steps: str | None = None
    location: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class InteractionOut(ORMModel):
    id: UUID
    customer_id: UUID
    created_by_id: UUID
    lead_id: UUID | None
    case_id: UUID | None
    channel: InteractionChannel
    direction: InteractionDirection
    occurred_at: datetime
    summary: str
    outcome: str | None
    customer_interest: str | None
    next_steps: str | None
    location: str | None
    metadata_json: dict
    created_at: datetime


class LeadCreate(BaseModel):
    customer_id: UUID
    title: str
    description: str | None = None
    product_or_service: str | None = None
    source: str | None = None
    status: LeadStatus = LeadStatus.new
    priority: str = "normal"
    estimated_value: int | None = None
    owner_id: UUID | None = None
    team_id: UUID | None = None
    expected_close_at: datetime | None = None


class LeadUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    product_or_service: str | None = None
    source: str | None = None
    status: LeadStatus | None = None
    priority: str | None = None
    estimated_value: int | None = None
    owner_id: UUID | None = None
    team_id: UUID | None = None
    expected_close_at: datetime | None = None
    close_reason: str | None = None


class LeadOut(ORMModel):
    id: UUID
    customer_id: UUID
    title: str
    description: str | None
    product_or_service: str | None
    source: str | None
    status: LeadStatus
    priority: str
    estimated_value: int | None
    owner_id: UUID | None
    team_id: UUID | None
    expected_close_at: datetime | None
    close_reason: str | None
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    customer_id: UUID
    title: str
    description: str
    category: str | None = None
    priority: str = "normal"
    status: CaseStatus = CaseStatus.open
    owner_id: UUID | None = None
    team_id: UUID | None = None
    due_at: datetime | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    status: CaseStatus | None = None
    owner_id: UUID | None = None
    team_id: UUID | None = None
    due_at: datetime | None = None
    resolution: str | None = None


class CaseOut(ORMModel):
    id: UUID
    customer_id: UUID
    title: str
    description: str
    category: str | None
    priority: str
    status: CaseStatus
    owner_id: UUID | None
    team_id: UUID | None
    due_at: datetime | None
    resolution: str | None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    customer_id: UUID
    lead_id: UUID | None = None
    case_id: UUID | None = None
    title: str
    description: str | None = None
    owner_id: UUID
    due_at: datetime
    priority: str = "normal"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    owner_id: UUID | None = None
    due_at: datetime | None = None
    priority: str | None = None
    status: TaskStatus | None = None


class TaskOut(ORMModel):
    id: UUID
    customer_id: UUID
    lead_id: UUID | None
    case_id: UUID | None
    title: str
    description: str | None
    owner_id: UUID
    due_at: datetime
    priority: str
    status: TaskStatus
    completed_at: datetime | None
    created_at: datetime


class TransferCreate(BaseModel):
    entity_type: str = Field(pattern="^(customer|lead|case)$")
    entity_id: UUID
    to_team_id: UUID | None = None
    to_user_id: UUID | None = None
    reason: str = Field(min_length=3)


class TransferOut(ORMModel):
    id: UUID
    customer_id: UUID
    entity_type: str
    entity_id: UUID
    from_team_id: UUID | None
    to_team_id: UUID | None
    from_user_id: UUID | None
    to_user_id: UUID | None
    requested_by_id: UUID
    reason: str
    status: str
    created_at: datetime
