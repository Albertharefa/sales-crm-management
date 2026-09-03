from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# BASE MODEL
# ============================================================

class CRMBaseModel(BaseModel):
    """
    Base model untuk seluruh CRM.
    Extra fields diperbolehkan agar data lama tidak rusak
    ketika ada field tambahan dari database.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        from_attributes=True,
    )


# ============================================================
# GENERIC PAGINATION
# ============================================================

class Paginated(CRMBaseModel):
    items: List[Any] = Field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0


# ============================================================
# AUTHENTICATION
# ============================================================

class LoginRequest(CRMBaseModel):
    email: str
    password: str


class LoginResponse(CRMBaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[Any] = None


class UserPublic(CRMBaseModel):
    id: str
    email: str
    name: str
    role: str = "SALES"

    is_active: bool = True


class UserCreate(CRMBaseModel):
    email: str
    name: str
    password: str
    role: str = "SALES"
    is_active: bool = True


class UserUpdate(CRMBaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================
# CUSTOMER
# ============================================================

class CustomerCreate(CRMBaseModel):
    name: str

    company: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = "Indonesia"

    status: Optional[str] = "Active"

    notes: Optional[str] = None


class CustomerUpdate(CRMBaseModel):
    name: Optional[str] = None

    company: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None

    status: Optional[str] = None
    notes: Optional[str] = None


class Customer(CRMBaseModel):
    id: str
    customer_id: Optional[str] = None

    name: str

    company: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = "Indonesia"

    status: Optional[str] = "Active"

    notes: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# CUSTOMER CONTACT
# ============================================================

class ContactCreate(CRMBaseModel):
    name: str

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    notes: Optional[str] = None

    is_primary: bool = False


class ContactUpdate(CRMBaseModel):
    name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    notes: Optional[str] = None

    is_primary: Optional[bool] = None


class Contact(CRMBaseModel):
    id: str
    contact_id: Optional[str] = None

    customer_id: str

    name: str

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    notes: Optional[str] = None

    is_primary: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# ACTIVITIES
# ============================================================

class ActivityCreate(CRMBaseModel):
    customer_id: Optional[str] = None

    subject: str
    activity_type: str = "Other"

    date: Optional[date] = None

    description: Optional[str] = None
    status: str = "Open"

    next_follow_up: Optional[date] = None


class ActivityUpdate(CRMBaseModel):
    customer_id: Optional[str] = None

    subject: Optional[str] = None
    activity_type: Optional[str] = None

    date: Optional[date] = None

    description: Optional[str] = None
    status: Optional[str] = None

    next_follow_up: Optional[date] = None


class Activity(CRMBaseModel):
    id: str
    activity_id: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    subject: str
    activity_type: str = "Other"

    date: Optional[date] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    next_follow_up: Optional[date] = None

    status: str = "Open"

    description: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# TASK
# ============================================================

class TaskCreate(CRMBaseModel):
    title: str

    description: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    due_date: Optional[date] = None

    priority: str = "Medium"
    status: str = "Open"


class TaskUpdate(CRMBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    due_date: Optional[date] = None

    priority: Optional[str] = None
    status: Optional[str] = None


class Task(CRMBaseModel):
    id: str

    task_id: Optional[str] = None

    title: str

    description: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    due_date: Optional[date] = None

    priority: str = "Medium"
    status: str = "Open"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# PRODUCTS
# ============================================================

class ProductCreate(CRMBaseModel):
    name: str

    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None

    description: Optional[str] = None

    unit: Optional[str] = None

    price: Optional[float] = 0
    cost: Optional[float] = 0

    currency: str = "IDR"

    status: str = "Active"


class ProductUpdate(CRMBaseModel):
    name: Optional[str] = None

    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None

    description: Optional[str] = None

    unit: Optional[str] = None

    price: Optional[float] = None
    cost: Optional[float] = None

    currency: Optional[str] = None

    status: Optional[str] = None


class Product(CRMBaseModel):
    id: str

    product_id: Optional[str] = None

    name: str

    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None

    description: Optional[str] = None

    unit: Optional[str] = None

    price: Optional[float] = 0
    cost: Optional[float] = 0

    currency: str = "IDR"

    status: str = "Active"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# QUOTATIONS
# ============================================================

class QuotationItem(CRMBaseModel):
    product_id: Optional[str] = None

    product_name: Optional[str] = None
    description: Optional[str] = None

    quantity: float = 1

    unit_price: float = 0

    discount: float = 0

    subtotal: float = 0


class QuotationCreate(CRMBaseModel):
    customer_id: Optional[str] = None

    quotation_number: Optional[str] = None

    quotation_date: Optional[date] = None

    valid_until: Optional[date] = None

    currency: str = "IDR"

    items: List[QuotationItem] = Field(default_factory=list)

    subtotal: float = 0
    discount: float = 0
    tax: float = 0
    grand_total: float = 0

    status: str = "Draft"

    notes: Optional[str] = None


class QuotationUpdate(CRMBaseModel):
    customer_id: Optional[str] = None

    quotation_date: Optional[date] = None
    valid_until: Optional[date] = None

    currency: Optional[str] = None

    items: Optional[List[QuotationItem]] = None

    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tax: Optional[float] = None
    grand_total: Optional[float] = None

    status: Optional[str] = None

    notes: Optional[str] = None


class Quotation(CRMBaseModel):
    id: str

    quotation_id: Optional[str] = None
    quotation_number: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    quotation_date: Optional[date] = None
    valid_until: Optional[date] = None

    currency: str = "IDR"

    items: List[QuotationItem] = Field(default_factory=list)

    subtotal: float = 0
    discount: float = 0
    tax: float = 0
    grand_total: float = 0

    status: str = "Draft"

    notes: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# ORDERS
# ============================================================

class OrderItem(CRMBaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None

    quantity: float = 1

    unit_price: float = 0

    subtotal: float = 0


class OrderCreate(CRMBaseModel):
    customer_id: Optional[str] = None

    order_number: Optional[str] = None

    order_date: Optional[date] = None

    items: List[OrderItem] = Field(default_factory=list)

    subtotal: float = 0
    discount: float = 0
    tax: float = 0
    grand_total: float = 0

    status: str = "Open"

    notes: Optional[str] = None


class OrderUpdate(CRMBaseModel):
    customer_id: Optional[str] = None

    order_date: Optional[date] = None

    items: Optional[List[OrderItem]] = None

    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tax: Optional[float] = None
    grand_total: Optional[float] = None

    status: Optional[str] = None

    notes: Optional[str] = None


class Order(CRMBaseModel):
    id: str

    order_id: Optional[str] = None
    order_number: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    order_date: Optional[date] = None

    items: List[OrderItem] = Field(default_factory=list)

    subtotal: float = 0
    discount: float = 0
    tax: float = 0
    grand_total: float = 0

    status: str = "Open"

    notes: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# PIPELINE / OPPORTUNITY
# ============================================================

class PipelineCreate(CRMBaseModel):
    customer_id: Optional[str] = None

    name: str

    description: Optional[str] = None

    stage: str = "Prospecting"

    probability: float = 0

    expected_value: float = 0

    expected_close_date: Optional[date] = None

    status: str = "Open"


class PipelineUpdate(CRMBaseModel):
    customer_id: Optional[str] = None

    name: Optional[str] = None

    description: Optional[str] = None

    stage: Optional[str] = None

    probability: Optional[float] = None

    expected_value: Optional[float] = None

    expected_close_date: Optional[date] = None

    status: Optional[str] = None


class Pipeline(CRMBaseModel):
    id: str

    opportunity_id: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    name: str

    description: Optional[str] = None

    stage: str = "Prospecting"

    probability: float = 0

    expected_value: float = 0

    expected_close_date: Optional[date] = None

    status: str = "Open"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# DASHBOARD
# ============================================================

class DashboardMetrics(CRMBaseModel):
    total_customers: int = 0
    total_contacts: int = 0

    total_activities: int = 0
    total_tasks: int = 0

    total_products: int = 0

    total_quotations: int = 0
    total_orders: int = 0

    total_pipeline: float = 0

    open_pipeline: float = 0
    won_pipeline: float = 0
    lost_pipeline: float = 0

    total_sales: float = 0

    open_tasks: int = 0
    overdue_tasks: int = 0

    activities_today: int = 0

    conversion_rate: float = 0

    # Memungkinkan dashboard menambahkan metrik lain
    # tanpa merusak response model.
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        from_attributes=True,
    )


# ============================================================
# FILE UPLOAD
# ============================================================

class UploadResponse(CRMBaseModel):
    """
    Response standar upload file.

    Dibuat fleksibel supaya routers.uploads dapat melakukan
    import tanpa menyebabkan deployment gagal.
    """

    id: Optional[str] = None

    filename: Optional[str] = None
    original_filename: Optional[str] = None

    file_name: Optional[str] = None

    url: Optional[str] = None
    file_url: Optional[str] = None

    path: Optional[str] = None

    content_type: Optional[str] = None

    size: Optional[int] = None
    file_size: Optional[int] = None

    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    message: Optional[str] = None

    success: bool = True


# ============================================================
# GENERIC API RESPONSE
# ============================================================

class APIResponse(CRMBaseModel):
    success: bool = True

    message: Optional[str] = None

    data: Optional[Any] = None


# ============================================================
# HEALTH / SYSTEM
# ============================================================

class HealthResponse(CRMBaseModel):
    status: str = "ok"

    database: Optional[str] = None

    version: Optional[str] = None

    timestamp: Optional[datetime] = None
