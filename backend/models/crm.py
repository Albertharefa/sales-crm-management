# ============================================================
# SALES CRM MANAGEMENT
# models/crm.py
#
# CENTRAL CRM PYDANTIC MODELS
# IMPORTANT:
# - NO router imports
# - NO database imports
# - NO circular dependencies
# - All CRM shared models live here
# ============================================================

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# ============================================================
# COMMON BASE
# ============================================================

class CRMBaseModel(BaseModel):
    """
    Base model used by CRM models.

    extra="ignore" prevents MongoDB fields that are not part
    of the API schema from breaking response validation.
    """

    model_config = ConfigDict(
        extra="ignore"
    )


# ============================================================
# AUTH
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserPublic(CRMBaseModel):
    id: str
    user_id: str
    name: str
    email: EmailStr
    role: str

    manager_id: Optional[str] = None
    phone: Optional[str] = None

    status: str = "Active"

    last_login: Optional[datetime] = None


class UserCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    role: str

    manager_id: Optional[str] = None
    phone: Optional[str] = None

    status: str = "Active"

    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

    manager_id: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
# CUSTOMER
# ============================================================

class Customer(CRMBaseModel):
    id: str
    customer_id: str

    name: str

    company: Optional[str] = None

    industry: str = "Manufacturing"
    city: str = "Jakarta"
    province: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    pic_name: Optional[str] = None
    pic_position: Optional[str] = None

    source: Optional[str] = None

    status: str = "Active"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2)

    industry: str = "Manufacturing"
    source: Optional[str] = None

    city: str = "Jakarta"
    province: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    pic_name: Optional[str] = None
    pic_position: Optional[str] = None

    status: str = "Active"

    sales_id: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value):
        if value == "":
            return None
        return value


class CustomerUpdate(BaseModel):
    name: Optional[str] = None

    industry: Optional[str] = None
    source: Optional[str] = None

    city: Optional[str] = None
    province: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    pic_name: Optional[str] = None
    pic_position: Optional[str] = None

    status: Optional[str] = None

    sales_id: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value):
        if value == "":
            return None
        return value


# ============================================================
# CONTACT
# ============================================================

class Contact(CRMBaseModel):
    id: str
    contact_id: Optional[str] = None

    customer_id: str
    customer_name: Optional[str] = None

    first_name: str
    last_name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[EmailStr] = None
    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[EmailStr] = None
    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value):
        if value == "":
            return None
        return value


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[EmailStr] = None
    mobile: Optional[str] = None

    contact_type: Optional[str] = None

    is_decision_maker: Optional[bool] = None

    status: Optional[str] = None

    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value):
        if value == "":
            return None
        return value


# ============================================================
# OPPORTUNITY
# ============================================================

class Opportunity(CRMBaseModel):
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
    updated_at: Optional[datetime] = None


class OpportunityCreate(BaseModel):
    name: str = Field(min_length=2)

    customer_id: str

    value: float = Field(
        default=0,
        ge=0,
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


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None

    customer_id: Optional[str] = None

    value: Optional[float] = Field(
        default=None,
        ge=0,
    )

    probability: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    stage: Optional[str] = None

    target_close: Optional[date] = None

    brand: Optional[str] = None
    product: Optional[str] = None

    next_action: Optional[str] = None

    description: Optional[str] = None

    loss_reason: Optional[str] = None


# ============================================================
# ACTIVITY
# ============================================================

class Activity(CRMBaseModel):
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


class ActivityUpdate(BaseModel):
    subject: Optional[str] = None

    activity_type: Optional[str] = None

    date: Optional[date] = None

    customer_id: Optional[str] = None

    next_follow_up: Optional[date] = None

    status: Optional[str] = None

    description: Optional[str] = None


# ============================================================
# TASK
# ============================================================

class Task(CRMBaseModel):
    id: str

    task_id: Optional[str] = None

    title: str

    due_date: date

    priority: str = "Medium"

    status: str = "Pending"

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    opportunity_id: Optional[str] = None
    opportunity_name: Optional[str] = None

    assigned_user: Optional[str] = None
    assigned_user_id: Optional[str] = None

    description: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=2
    )

    due_date: date

    priority: str = "Medium"

    status: str = "Pending"

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    opportunity_id: Optional[str] = None
    opportunity_name: Optional[str] = None

    assigned_user: Optional[str] = None
    assigned_user_id: Optional[str] = None

    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None

    due_date: Optional[date] = None

    priority: Optional[str] = None

    status: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    opportunity_id: Optional[str] = None
    opportunity_name: Optional[str] = None

    assigned_user: Optional[str] = None
    assigned_user_id: Optional[str] = None

    description: Optional[str] = None


# ============================================================
# PRODUCT
# ============================================================

class Product(CRMBaseModel):
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
    updated_at: Optional[datetime] = None


class ProductCreate(BaseModel):
    code: str = Field(
        min_length=1
    )

    name: str = Field(
        min_length=2
    )

    brand: Optional[str] = None

    category: str = "Automation"

    unit: str = "pcs"

    default_price: float = Field(
        default=0,
        ge=0,
    )

    supplier: Optional[str] = None

    status: str = "Active"

    description: Optional[str] = None


class ProductUpdate(BaseModel):
    code: Optional[str] = None

    name: Optional[str] = None

    brand: Optional[str] = None

    category: Optional[str] = None

    unit: Optional[str] = None

    default_price: Optional[float] = Field(
        default=None,
        ge=0,
    )

    supplier: Optional[str] = None

    status: Optional[str] = None

    description: Optional[str] = None


# ============================================================
# DASHBOARD
# ============================================================

class DashboardGroupMetric(CRMBaseModel):
    name: str
    count: int = 0
    value: float = 0


class DashboardMonthlyMetric(CRMBaseModel):
    month: str
    target: float = 0
    actual: float = 0
    achievement: float = 0


class DashboardRecentActivity(CRMBaseModel):
    id: str

    subject: str

    activity_type: str

    customer_name: Optional[str] = None
    sales_name: Optional[str] = None

    date: Optional[str] = None

    status: str


class DashboardDealRisk(CRMBaseModel):
    id: str

    opportunity_id: str

    name: str

    customer_name: str

    sales_name: Optional[str] = None

    value: float

    stage: str

    expected_close: Optional[str] = None

    reason: str


class DashboardMetrics(CRMBaseModel):
    total_customer: int = 0
    total_contacts: int = 0

    total_leads: int = 0
    total_opportunities: int = 0

    open_pipeline: float = 0
    weighted_pipeline: float = 0

    won_value: float = 0
    lost_value: float = 0

    win_rate: float = 0

    total_quotation: int = 0
    active_quotations: int = 0

    quotation_value: float = 0

    total_po: int = 0
    po_value: float = 0

    open_orders: int = 0
    completed_orders: int = 0
    overdue_orders: int = 0

    activities: int = 0
    overdue_activities: int = 0

    sales_target: float = 0
    target_achievement: float = 0

    pipeline_by_stage: List[DashboardGroupMetric] = Field(
        default_factory=list
    )

    pipeline_by_salesperson: List[DashboardGroupMetric] = Field(
        default_factory=list
    )

    monthly_sales_performance: List[DashboardMonthlyMetric] = Field(
        default_factory=list
    )

    recent_activities: List[DashboardRecentActivity] = Field(
        default_factory=list
    )

    deal_risks: List[DashboardDealRisk] = Field(
        default_factory=list
    )

    generated_at: datetime


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(CRMBaseModel):
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

    open_pipeline: float = 0

    weighted: float = 0

    won: float = 0

    po: int = 0

    po_value: float = 0

    activities: int = 0

    indent: int = 0

    overdue: int = 0


# ============================================================
# GENERIC RESPONSE
# ============================================================

class MessageResponse(BaseModel):
    status: str
    message: str


# ============================================================
# MODULE READY
# ============================================================

print("INFO: ✓ models.crm loaded")
