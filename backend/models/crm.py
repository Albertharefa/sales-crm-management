from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CUSTOMER
# ============================================================

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    customer_id: str

    name: str = ""
    company_name: str = ""
    company: Optional[str] = None

    industry: str = "Manufacturing"
    city: str = "Jakarta"
    province: str = ""

    phone: Optional[str] = None
    email: Optional[str] = None

    pic_name: Optional[str] = None
    pic_position: Optional[str] = None

    status: str = "Active"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CustomerCreate(BaseModel):
    name: str = ""

    company_name: Optional[str] = None
    company: Optional[str] = None

    industry: str = "Manufacturing"
    city: str = "Jakarta"
    province: str = ""

    phone: Optional[str] = None
    email: Optional[str] = None

    pic_name: Optional[str] = None
    pic_position: Optional[str] = None

    status: str = "Active"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
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

    status: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# CONTACT
# ============================================================

class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    customer_id: str

    first_name: str = ""
    last_name: str = ""

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContactCreate(BaseModel):
    first_name: str = ""
    last_name: str = ""

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None


# ============================================================
# OPPORTUNITY
# ============================================================

class Opportunity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    opportunity_id: str

    name: str

    customer_id: str
    customer_name: str

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    value: float = 0

    probability: float = Field(
        default=50,
        ge=0,
        le=100,
    )

    stage: str = "Lead"

    target_close: Optional[date] = None

    brand: Optional[str] = None
    product: Optional[str] = None

    next_action: Optional[str] = None

    description: Optional[str] = None

    loss_reason: Optional[str] = None

    created_at: datetime


class OpportunityCreate(BaseModel):
    name: str = Field(
        min_length=2
    )

    customer_id: str

    value: float = Field(
        ge=0
    )

    probability: float = Field(
        default=50,
        ge=0,
        le=100,
    )

    stage: str = "Lead"

    target_close: Optional[date] = None

    brand: Optional[str] = None
    product: Optional[str] = None

    next_action: Optional[str] = None

    description: Optional[str] = None

    loss_reason: Optional[str] = None


# ============================================================
# ACTIVITY
# ============================================================

class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str

    activity_id: str

    subject: str

    activity_type: str = "Call"

    date: date

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    next_follow_up: Optional[date] = None

    status: str = "Open"

    description: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None


class ActivityCreate(BaseModel):
    subject: str = Field(
        min_length=2
    )

    activity_type: str = "Call"

    date: date

    customer_id: Optional[str] = None

    next_follow_up: Optional[date] = None

    status: str = "Open"

    description: Optional[str] = None


# ============================================================
# TASK
# ============================================================

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str

    task_id: Optional[str] = None

    title: str

    due_date: date

    priority: str = "Medium"

    status: str = "Pending"

    customer_name: Optional[str] = None

    opportunity_name: Optional[str] = None

    assigned_user: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=2
    )

    due_date: date

    priority: str = "Medium"

    status: str = "Pending"

    customer_name: Optional[str] = None

    opportunity_name: Optional[str] = None

    assigned_user: Optional[str] = None


# ============================================================
# PRODUCT
# ============================================================

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str

    code: str

    name: str

    brand: Optional[str] = None

    category: str = "Automation"

    unit: str = "pcs"

    default_price: float = 0

    supplier: Optional[str] = None

    status: str = "Active"

    description: Optional[str] = None

    created_at: datetime


class ProductCreate(BaseModel):
    code: str = Field(
        min_length=2
    )

    name: str = Field(
        min_length=2
    )

    brand: Optional[str] = None

    category: str = "Automation"

    unit: str = "pcs"

    default_price: float = Field(
        ge=0
    )

    supplier: Optional[str] = None

    status: str = "Active"

    description: Optional[str] = None


# ============================================================
# QUOTATION
# ============================================================

class QuotationItem(BaseModel):
    product_id: Optional[str] = None

    description: str

    quantity: float = Field(
        gt=0
    )

    unit_price: float = Field(
        ge=0
    )

    discount: float = Field(
        default=0,
        ge=0,
    )

    tax: float = Field(
        default=11,
        ge=0,
        le=100,
    )


class Quotation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str

    number: str

    date: date

    customer_id: str

    customer_name: str

    sales_name: Optional[str] = None

    items: List[QuotationItem]

    payment_term: Optional[str] = None

    delivery_term: Optional[str] = None

    subtotal: float

    discount_total: float

    tax_total: float

    grand_total: float

    status: str = "Draft"

    notes: Optional[str] = None

    created_at: datetime


class QuotationCreate(BaseModel):
    customer_id: str

    date: date

    valid_until: Optional[date] = None

    payment_term: Optional[str] = None

    delivery_term: Optional[str] = None

    items: List[QuotationItem] = Field(
        min_length=1
    )

    notes: Optional[str] = None


# ============================================================
# PURCHASE ORDER
# ============================================================

class PurchaseOrderItem(BaseModel):
    product_id: Optional[str] = None

    description: str

    quantity: float = Field(
        gt=0
    )

    unit_price: float = Field(
        ge=0
    )


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str

    po_number: str

    date: date

    customer_id: str

    customer_name: str

    quotation_number: Optional[str] = None

    sales_name: Optional[str] = None

    items: List[PurchaseOrderItem]

    total: float

    status: str = "Received"

    eta: Optional[date] = None

    supplier: Optional[str] = None

    document_name: Optional[str] = None

    shipping_address: Optional[str] = None

    created_at: datetime


class PurchaseOrderCreate(BaseModel):
    po_number: str = Field(
        min_length=2
    )

    customer_id: str

    date: date

    status: str = "Received"

    items: List[PurchaseOrderItem] = Field(
        min_length=1
    )

    eta: Optional[date] = None

    supplier: Optional[str] = None

    document_name: Optional[str] = None

    shipping_address: Optional[str] = None


# ============================================================
# DASHBOARD
# ============================================================

class DashboardGroupMetric(BaseModel):
    name: str
    count: int
    value: float


class DashboardMonthlyMetric(BaseModel):
    month: str
    label: str
    actual: float
    target: float


class DashboardRecentActivity(BaseModel):
    id: str
    subject: str
    activity_type: str

    customer_name: Optional[str] = None
    sales_name: Optional[str] = None

    date: Optional[str] = None

    status: str


class DashboardDealRisk(BaseModel):
    id: str

    opportunity_id: str

    name: str

    customer_name: str

    sales_name: Optional[str] = None

    value: float

    stage: str

    expected_close: Optional[str] = None

    reason: str


class DashboardMetrics(BaseModel):
    total_customer: int
    total_contacts: int

    total_leads: int
    total_opportunities: int

    open_pipeline: float
    weighted_pipeline: float

    won_value: float
    lost_value: float

    win_rate: float

    total_quotation: int
    active_quotations: int

    quotation_value: float

    total_po: int
    po_value: float

    open_orders: int
    completed_orders: int
    overdue_orders: int

    activities: int
    overdue_activities: int

    sales_target: float
    target_achievement: float

    pipeline_by_stage: List[DashboardGroupMetric]

    pipeline_by_salesperson: List[DashboardGroupMetric]

    monthly_sales_performance: List[DashboardMonthlyMetric]

    recent_activities: List[DashboardRecentActivity]

    deal_risks: List[DashboardDealRisk]

    generated_at: datetime


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str

    user_name: str

    action: str

    module: str

    record_id: Optional[str] = None

    changes: Optional[Dict[str, Any]] = None

    created_at: datetime


# ============================================================
# PAGINATION
# ============================================================

class Paginated(BaseModel):
    items: List[Any]

    page: int

    page_size: int

    total: int


# ============================================================
# UPLOAD
# ============================================================

class UploadResponse(BaseModel):
    id: str

    file_name: str

    content_type: str

    size: int

    url: str


# ============================================================
# OPTIONS
# ============================================================

class OptionItem(BaseModel):
    id: str

    name: str

    role: Optional[str] = None

    default_price: Optional[float] = None


class OptionsResponse(BaseModel):
    customers: List[OptionItem]

    products: List[OptionItem]

    users: List[OptionItem]


# ============================================================
# SALES TEAM
# ============================================================

class SalesTeamMetric(BaseModel):
    sales: str

    role: str

    manager: str

    open_pipeline: float

    weighted: float

    won: float

    po: int

    po_value: float

    activities: int

    indent: int

    overdue: int
