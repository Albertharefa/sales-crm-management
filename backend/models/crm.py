from __future__ import annotations

from typing import TypeVar, Generic, List, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

class CRMBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", arbitrary_types_allowed=True)

class Paginated(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

class OpportunityBase(CRMBaseModel):
    title: str
    customer_id: str
    value: float = 0
    stage: str = "Lead"
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
    id: str
    opportunity_id: Optional[str] = None
    customer_name: Optional[str] = None
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    loss_reason: Optional[str] = None
    created_at: datetime

Opportunity = OpportunityInDB

class QuotationItem(CRMBaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: int = 1
    unit_price: float = 0
    discount: float = 0
    tax: float = 0
    total: float = 0

class QuotationBase(CRMBaseModel):
    customer_id: str
    opportunity_id: Optional[str] = None
    items: List[QuotationItem]
    subtotal: float = 0
    tax: float = 0
    total_amount: float = 0
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
    id: str
    number: Optional[str] = None
    customer_name: Optional[str] = None
    sales_name: Optional[str] = None
    status: str = "Draft"
    discount_total: float = 0
    tax_total: float = 0
    grand_total: float = 0
    created_at: datetime

Quotation = QuotationInDB

class PurchaseOrderBase(CRMBaseModel):
    customer_id: str
    items: List[QuotationItem]
    total: float = 0
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    po_number: Optional[str] = None
    status: str = "Received"

class PurchaseOrderUpdate(CRMBaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderInDB(PurchaseOrderBase):
    id: str
    po_number: str
    customer_name: Optional[str] = None
    sales_name: Optional[str] = None
    status: str = "Received"
    created_at: datetime

PurchaseOrder = PurchaseOrderInDB

class ActivityBase(CRMBaseModel):
    subject: str
    activity_type: str = "Call"
    customer_id: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    status: str = "Open"
    next_follow_up: Optional[datetime] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(CRMBaseModel):
    subject: Optional[str] = None
    activity_type: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None
    next_follow_up: Optional[datetime] = None

class ActivityInDB(ActivityBase):
    id: str
    activity_id: Optional[str] = None
    customer_name: Optional[str] = None
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    created_at: datetime

Activity = ActivityInDB
Task = ActivityInDB
TaskCreate = ActivityCreate
TaskUpdate = ActivityUpdate

class UserCreate(CRMBaseModel):
    email: str
    name: str
    role: str = "SALES"
    status: str = "Active"
    password: str

class UserPublic(CRMBaseModel):
    id: str
    email: str
    name: str = ""
    role: str = "SALES"
    status: str = "Active"
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class LoginRequest(CRMBaseModel):
    email: str
    password: str

class OptionsResponse(CRMBaseModel):
    options: Optional[List[Any]] = None
    customers: Optional[List[Any]] = None
    products: Optional[List[Any]] = None
    users: Optional[List[Any]] = None

class SalesTeamMetric(CRMBaseModel):
    sales: Optional[str] = None
    role: Optional[str] = None
    manager: Optional[str] = None
    open_pipeline: float = 0
    weighted: float = 0
    won: float = 0
    po: int = 0
    po_value: float = 0
    activities: int = 0
    indent: int = 0
    overdue: int = 0
