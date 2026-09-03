from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# BASE MODEL
# ============================================================

class CRMBase(BaseModel):
    """
    Base model untuk CRM.

    extra="allow" sengaja digunakan agar model tetap kompatibel
    dengan field tambahan yang mungkin sudah tersimpan di MongoDB.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


# ============================================================
# PAGINATION
# ============================================================

class Paginated(CRMBase):
    items: list[Any] = Field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0


# ============================================================
# AUTHENTICATION / USERS
# ============================================================

class LoginRequest(CRMBase):
    email: str
    password: str


class LoginResponse(CRMBase):
    user: Optional[Any] = None
    message: str = "Login successful"


class UserPublic(CRMBase):
    id: str
    name: str
    email: str

    role: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None

    is_active: bool = True


class UserCreate(CRMBase):
    name: str
    email: str
    password: str

    role: str = "sales"
    department: Optional[str] = None
    position: Optional[str] = None


class UserUpdate(CRMBase):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    role: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None

    is_active: Optional[bool] = None


# ============================================================
# CUSTOMER
# ============================================================

class Customer(CRMBase):
    id: str
    customer_id: Optional[str] = None

    name: str
    company_name: Optional[str] = None

    customer_type: Optional[str] = None
    industry: Optional[str] = None
    segment: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: str = "active"
    priority: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CustomerCreate(CRMBase):
    name: str

    company_name: Optional[str] = None

    customer_type: Optional[str] = None
    industry: Optional[str] = None
    segment: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: str = "active"
    priority: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None


class CustomerUpdate(CRMBase):
    name: Optional[str] = None
    company_name: Optional[str] = None

    customer_type: Optional[str] = None
    industry: Optional[str] = None
    segment: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: Optional[str] = None
    priority: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None


# ============================================================
# CONTACT
# ============================================================

class Contact(CRMBase):
    id: str
    contact_id: Optional[str] = None

    customer_id: str
    customer_name: Optional[str] = None

    first_name: str
    last_name: str

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None

    contact_type: Optional[str] = None

    is_decision_maker: bool = False
    is_primary: bool = False

    status: str = "active"

    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContactCreate(CRMBase):
    first_name: str
    last_name: str

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None

    contact_type: Optional[str] = None

    is_decision_maker: bool = False
    is_primary: bool = False

    status: str = "active"

    notes: Optional[str] = None


class ContactUpdate(CRMBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None
    phone: Optional[str] = None

    contact_type: Optional[str] = None

    is_decision_maker: Optional[bool] = None
    is_primary: Optional[bool] = None

    status: Optional[str] = None

    notes: Optional[str] = None


# ============================================================
# ACTIVITIES
# ============================================================

class Activity(CRMBase):
    id: str
    activity_id: Optional[str] = None

    subject: str
    activity_type: str

    date: Optional[date] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    contact_id: Optional[str] = None
    contact_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    next_follow_up: Optional[date] = None

    status: str = "open"

    description: Optional[str] = None
    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ActivityCreate(CRMBase):
    customer_id: Optional[str] = None
    contact_id: Optional[str] = None

    subject: str
    activity_type: str

    date: Optional[date] = None
    next_follow_up: Optional[date] = None

    description: Optional[str] = None
    status: str = "open"

    notes: Optional[str] = None


# ============================================================
# TASKS
# ============================================================

class Task(CRMBase):
    id: str
    task_id: Optional[str] = None

    title: str
    description: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    contact_id: Optional[str] = None
    contact_name: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    due_date: Optional[date] = None

    priority: str = "medium"
    status: str = "open"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskCreate(CRMBase):
    title: str

    description: Optional[str] = None

    customer_id: Optional[str] = None
    contact_id: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    due_date: Optional[date] = None

    priority: str = "medium"
    status: str = "open"


class TaskUpdate(CRMBase):
    title: Optional[str] = None
    description: Optional[str] = None

    customer_id: Optional[str] = None
    contact_id: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    due_date: Optional[date] = None

    priority: Optional[str] = None
    status: Optional[str] = None


# ============================================================
# PIPELINE / OPPORTUNITY
# ============================================================

class Pipeline(CRMBase):
    id: str
    pipeline_id: Optional[str] = None

    name: str

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    stage: Optional[str] = None
    status: str = "open"

    amount: float = 0
    probability: float = 0

    expected_close_date: Optional[date] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PipelineCreate(CRMBase):
    name: str

    customer_id: Optional[str] = None

    stage: Optional[str] = None
    status: str = "open"

    amount: float = 0
    probability: float = 0

    expected_close_date: Optional[date] = None

    description: Optional[str] = None
    notes: Optional[str] = None


class PipelineUpdate(CRMBase):
    name: Optional[str] = None

    customer_id: Optional[str] = None

    stage: Optional[str] = None
    status: Optional[str] = None

    amount: Optional[float] = None
    probability: Optional[float] = None

    expected_close_date: Optional[date] = None

    description: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# PRODUCTS
# ============================================================

class Product(CRMBase):
    id: str
    product_id: Optional[str] = None

    name: str

    brand: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None

    description: Optional[str] = None

    unit: Optional[str] = None

    price: float = 0
    currency: str = "IDR"

    status: str = "active"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductCreate(CRMBase):
    name: str

    brand: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None

    description: Optional[str] = None

    unit: Optional[str] = None

    price: float = 0
    currency: str = "IDR"

    status: str = "active"


class ProductUpdate(CRMBase):
    name: Optional[str] = None

    brand: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None

    description: Optional[str] = None

    unit: Optional[str] = None

    price: Optional[float] = None
    currency: Optional[str] = None

    status: Optional[str] = None


# ============================================================
# QUOTATIONS
# ============================================================

class Quotation(CRMBase):
    id: str
    quotation_id: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    quotation_number: Optional[str] = None
    subject: Optional[str] = None

    amount: float = 0
    currency: str = "IDR"

    status: str = "draft"

    valid_until: Optional[date] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuotationCreate(CRMBase):
    customer_id: Optional[str] = None

    quotation_number: Optional[str] = None
    subject: Optional[str] = None

    amount: float = 0
    currency: str = "IDR"

    status: str = "draft"

    valid_until: Optional[date] = None

    notes: Optional[str] = None


class QuotationUpdate(CRMBase):
    customer_id: Optional[str] = None

    quotation_number: Optional[str] = None
    subject: Optional[str] = None

    amount: Optional[float] = None
    currency: Optional[str] = None

    status: Optional[str] = None

    valid_until: Optional[date] = None

    notes: Optional[str] = None


# ============================================================
# ORDERS
# ============================================================

class Order(CRMBase):
    id: str
    order_id: Optional[str] = None

    order_number: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    amount: float = 0
    currency: str = "IDR"

    status: str = "open"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    order_date: Optional[date] = None

    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrderCreate(CRMBase):
    customer_id: Optional[str] = None

    order_number: Optional[str] = None

    amount: float = 0
    currency: str = "IDR"

    status: str = "open"

    order_date: Optional[date] = None

    notes: Optional[str] = None


class OrderUpdate(CRMBase):
    customer_id: Optional[str] = None

    order_number: Optional[str] = None

    amount: Optional[float] = None
    currency: Optional[str] = None

    status: Optional[str] = None

    order_date: Optional[date] = None

    notes: Optional[str] = None


# ============================================================
# UPLOADS
# ============================================================

class Upload(CRMBase):
    id: str

    file_id: Optional[str] = None

    filename: str
    original_filename: Optional[str] = None

    content_type: Optional[str] = None
    size: Optional[int] = None

    url: Optional[str] = None

    customer_id: Optional[str] = None
    activity_id: Optional[str] = None

    uploaded_by: Optional[str] = None
    uploaded_by_name: Optional[str] = None

    created_at: Optional[datetime] = None


class UploadCreate(CRMBase):
    filename: str

    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None

    url: Optional[str] = None

    customer_id: Optional[str] = None
    activity_id: Optional[str] = None


# ============================================================
# DASHBOARD METRICS
# ============================================================

class DashboardMetrics(CRMBase):
    """
    Dashboard response model.

    Dibuat fleksibel supaya kompatibel dengan dashboard.py
    dan memungkinkan penambahan KPI tanpa merusak API.
    """

    customers: int = 0
    contacts: int = 0

    activities: int = 0
    tasks: int = 0

    pipeline_value: float = 0
    quotation_value: float = 0
    order_value: float = 0

    open_tasks: int = 0
    overdue_tasks: int = 0

    won_deals: int = 0
    lost_deals: int = 0

    total_customers: int = 0
    total_contacts: int = 0
    total_activities: int = 0
    total_tasks: int = 0

    total_pipeline: float = 0
    total_quotations: float = 0
    total_orders: float = 0

    revenue: float = 0
    sales_target: float = 0
    sales_achievement: float = 0

    conversion_rate: float = 0
    win_rate: float = 0

    active_customers: int = 0
    active_opportunities: int = 0

    raw: Optional[dict[str, Any]] = None


# ============================================================
# DASHBOARD STATS
# ============================================================

class DashboardStats(CRMBase):
    customers: int = 0
    contacts: int = 0

    activities: int = 0
    tasks: int = 0

    pipeline_value: float = 0
    quotation_value: float = 0
    order_value: float = 0

    open_tasks: int = 0
    overdue_tasks: int = 0

    won_deals: int = 0
    lost_deals: int = 0


class SalesPerformance(CRMBase):
    sales_id: str
    sales_name: str

    customers: int = 0
    activities: int = 0
    tasks: int = 0

    pipeline_value: float = 0
    quotation_value: float = 0
    order_value: float = 0

    won: int = 0
    lost: int = 0


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(CRMBase):
    id: str

    user_id: Optional[str] = None
    user_name: Optional[str] = None

    action: str
    module: Optional[str] = None

    record_id: Optional[str] = None

    details: Optional[dict[str, Any]] = None

    created_at: Optional[datetime] = None
