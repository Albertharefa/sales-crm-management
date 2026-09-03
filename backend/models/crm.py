from __future__ import annotations

"""
CRM Models
Sales CRM Management System

Centralized Pydantic models for the CRM API.

IMPORTANT:
- This file must NOT import anything from routers.*
- Routers may import models from this file.
- Keep schemas centralized here to prevent circular imports.
"""

from typing import TypeVar, Generic, List, Any, Dict, Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar('T')

class Paginated(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int


# ==========================================
# BASE MODEL
# ==========================================

class CRMBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


# ==========================================
# CUSTOMER MODELS
# ==========================================

class CustomerBase(CRMBaseModel):
    name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = "active"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CRMBaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None


class CustomerInDB(CustomerBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


# ==========================================
# OPPORTUNITY / PIPELINE MODELS
# ==========================================

class OpportunityBase(CRMBaseModel):
    title: str
    customer_id: str
    value: float
    stage: str = "lead"  # lead, proposal, negotiation, won, lost
    probability: int = 10
    expected_close_date: Optional[date] = None
    notes: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(CRMBaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class OpportunityInDB(OpportunityBase):
    id: str = Field(alias="_id")
    owner_id: str
    status: str = "open"
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# QUOTATION MODELS
# ==========================================

class QuotationItem(CRMBaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: int
    unit_price: float
    discount: float = 0.0
    total: float


class QuotationBase(CRMBaseModel):
    customer_id: str
    opportunity_id: Optional[str] = None
    items: List[QuotationItem]
    subtotal: float
    tax: float = 0.0
    total_amount: float
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class QuotationCreate(QuotationBase):
    pass


class QuotationUpdate(CRMBaseModel):
    items: Optional[List[QuotationItem]] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class QuotationInDB(QuotationBase):
    id: str = Field(alias="_id")
    quotation_number: str
    status: str = "draft"  # draft, sent, accepted, rejected
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# ORDER MODELS
# ==========================================

class OrderBase(CRMBaseModel):
    quotation_id: Optional[str] = None
    customer_id: str
    items: List[QuotationItem]
    total_amount: float
    shipping_address: Optional[str] = None
    payment_terms: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(CRMBaseModel):
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_terms: Optional[str] = None


class OrderInDB(OrderBase):
    id: str = Field(alias="_id")
    order_number: str
    status: str = "pending"  # pending, processing, shipped, completed, cancelled
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# ACTIVITY & TASK MODELS
# ==========================================

class ActivityBase(CRMBaseModel):
    title: str
    activity_type: str = "call"  # call, meeting, email, task
    customer_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    completed: bool = False


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(CRMBaseModel):
    title: Optional[str] = None
    activity_type: Optional[str] = None
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class ActivityInDB(ActivityBase):
    id: str = Field(alias="_id")
    assigned_to: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# USER & AUTH MODELS
# ==========================================

class UserBase(CRMBaseModel):
    email: str
    full_name: str
    role: str = "sales_rep"  # admin, sales_manager, sales_rep
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime


class Token(CRMBaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(CRMBaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
