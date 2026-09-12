from datetime import date, datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId

T = TypeVar("T")

class CRMBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore", json_encoders={ObjectId: str})

class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

class OptionCustomer(CRMBaseModel):
    id: str
    name: str

class OptionProduct(CRMBaseModel):
    id: str
    name: str
    default_price: Optional[float] = None

class OptionUser(CRMBaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    role: str

class OptionsResponse(CRMBaseModel):
    customers: list[OptionCustomer] = Field(default_factory=list)
    products: list[OptionProduct] = Field(default_factory=list)
    users: list[OptionUser] = Field(default_factory=list)

class SalesTeamMetric(CRMBaseModel):
    # Fields used by the current Sales Team frontend/API response.
    sales: str = ""
    role: str = "SALES"
    manager: str = "-"
    target: float = 0
    gap_to_target: float = 0
    achievement: float = 0
    open_pipeline: float = 0
    weighted: float = 0
    coverage: float = 0
    won: float = 0
    won_count: int = 0
    lost_count: int = 0
    win_rate: float = 0
    po: int = 0
    po_value: float = 0
    activities: int = 0
    overdue_activities: int = 0
    indent: int = 0
    overdue: int = 0

    # Canonical identifiers retained for compatibility with older callers.
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    gap: float = 0

class UploadResponse(CRMBaseModel):
    id: str
    file_name: str
    content_type: str
    size: int
    url: str

class CustomerBase(CRMBaseModel):
    name: str
    company_name: str = ""
    company: Optional[str] = None
    industry: str = "Manufacturing"
    city: str = "Jakarta"
    province: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    source: Optional[str] = None
    status: str = "Active"
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class CustomerCreate(CustomerBase): pass
class CustomerUpdate(CRMBaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
class Customer(CustomerBase):
    id: str
    customer_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class OpportunityBase(CRMBaseModel):
    name: str
    customer_id: str
    sales_id: Optional[str] = None
    value: float = Field(ge=0)
    probability: int = Field(default=10, ge=0, le=100)
    stage: str = "Lead"
    target_close: Optional[date] = None
    brand: Optional[str] = None
    product: Optional[str] = None
    next_action: Optional[str] = None
    description: Optional[str] = None
    loss_reason: Optional[str] = None
class OpportunityCreate(OpportunityBase): pass
class OpportunityUpdate(CRMBaseModel):
    name: Optional[str] = None
    value: Optional[float] = None
    probability: Optional[int] = Field(default=None, ge=0, le=100)
    stage: Optional[str] = None
    target_close: Optional[date] = None
    brand: Optional[str] = None
    product: Optional[str] = None
    next_action: Optional[str] = None
    description: Optional[str] = None
    loss_reason: Optional[str] = None
class Opportunity(OpportunityBase):
    id: str
    opportunity_id: str
    customer_name: str = ""
    sales_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProductBase(CRMBaseModel):
    code: str
    name: str
    brand: Optional[str] = None
    category: str = "Other"
    unit: str = "pcs"
    default_price: float = Field(default=0, ge=0)
    supplier: Optional[str] = None
    status: str = "Active"
    description: Optional[str] = None
class ProductCreate(ProductBase): pass
class Product(ProductBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class QuotationItem(CRMBaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    total: Optional[float] = None
class QuotationCreate(CRMBaseModel):
    customer_id: str
    sales_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    date: date
    valid_until: Optional[date] = None
    payment_term: Optional[str] = None
    delivery_term: Optional[str] = None
    notes: Optional[str] = None
    items: list[QuotationItem] = Field(min_length=1)
class Quotation(QuotationCreate):
    id: str
    number: str
    customer_name: str = ""
    sales_name: Optional[str] = None
    customer_po_number: Optional[str] = None
    subtotal: float = 0
    discount_total: float = 0
    tax_total: float = 0
    grand_total: float = 0
    status: str = "Draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
class QuotationUpdate(CRMBaseModel):
    sales_id: Optional[str] = None
    items: Optional[list[QuotationItem]] = None
    status: Optional[str] = None
    valid_until: Optional[date] = None
    payment_term: Optional[str] = None
    delivery_term: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderItem(CRMBaseModel):
    product_id: Optional[str] = None
    description: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=11, ge=0)
class PurchaseOrderCreate(CRMBaseModel):
    po_number: str
    customer_id: str
    sales_id: Optional[str] = None
    date: date
    status: str = "Received"
    quotation_number: Optional[str] = None
    quotation_manual: bool = False
    items: list[PurchaseOrderItem] = Field(min_length=1)
    eta: Optional[date] = None
    payment_term: Optional[str] = None
    supplier: Optional[str] = None
    shipping_address: Optional[str] = None
    document_name: Optional[str] = None
class PurchaseOrder(PurchaseOrderCreate):
    id: str
    customer_name: str = ""
    sales_name: Optional[str] = None
    total: float = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
class PurchaseOrderUpdate(CRMBaseModel):
    status: Optional[str] = None
    eta: Optional[date] = None
    supplier: Optional[str] = None
    shipping_address: Optional[str] = None
    document_name: Optional[str] = None
class OrderBase(PurchaseOrderCreate): pass
class OrderCreate(PurchaseOrderCreate): pass
class OrderUpdate(PurchaseOrderUpdate): pass
class Order(PurchaseOrder): pass

class ActivityCreate(CRMBaseModel):
    subject: str
    activity_type: str = "Call"
    date: date
    customer_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    next_follow_up: Optional[date] = None
    status: str = "Open"
    description: Optional[str] = None
class Activity(ActivityCreate):
    id: str
    activity_id: str
    customer_name: Optional[str] = None
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
class ActivityUpdate(CRMBaseModel):
    subject: Optional[str] = None
    activity_type: Optional[str] = None
    date: Optional[date] = None
    next_follow_up: Optional[date] = None
    status: Optional[str] = None
    description: Optional[str] = None

class Task(CRMBaseModel):
    id: str
    title: str
    due_date: date
    priority: str = "Medium"
    status: str = "Pending"
    customer_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    assigned_user: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
TaskCreate = Task
TaskUpdate = ActivityUpdate

class UserBase(CRMBaseModel):
    email: str
    name: str
    role: str = "SALES"
    manager_id: Optional[str] = None
    phone: Optional[str] = None
    status: str = "Active"
class UserCreate(UserBase): password: str = Field(min_length=8)
class UserInDB(UserBase):
    id: str
    user_id: str
    password_hash: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class LoginRequest(CRMBaseModel):
    email: str
    password: str

class UserPublic(UserBase):
    id: str
    user_id: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None