"""
CRM Models
Sales CRM Management System

Centralized Pydantic models for the CRM API.

IMPORTANT:
- This file must NOT import anything from routers.*
- Routers may import models from this file.
- Keep schemas centralized here to prevent circular imports.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# BASE MODEL
# ============================================================

class CRMBaseModel(BaseModel):
    """
    Common base model.

    extra='allow' is intentional so existing MongoDB/API fields
    do not break validation when additional fields are present.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        from_attributes=True,
    )


# ============================================================
# PAGINATION
# ============================================================

class Paginated(CRMBaseModel):
    items: List[Any] = Field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0


# ============================================================
# CUSTOMER
# ============================================================

class CustomerBase(CRMBaseModel):
    customer_name: Optional[str] = None
    name: Optional[str] = None

    company_name: Optional[str] = None
    company: Optional[str] = None

    customer_code: Optional[str] = None
    code: Optional[str] = None

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

    status: Optional[str] = "Active"

    notes: Optional[str] = None
    description: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CRMBaseModel):
    customer_name: Optional[str] = None
    name: Optional[str] = None

    company_name: Optional[str] = None
    company: Optional[str] = None

    customer_code: Optional[str] = None
    code: Optional[str] = None

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

    notes: Optional[str] = None
    description: Optional[str] = None


class Customer(CustomerBase):
    id: Optional[str] = None
    customer_id: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# CONTACT
# ============================================================

class ContactBase(CRMBaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None

    job_title: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None

    notes: Optional[str] = None

    is_primary: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class Contact(ContactBase):
    id: Optional[str] = None
    contact_id: Optional[str] = None
    customer_id: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# ACTIVITY
# ============================================================

class ActivityBase(CRMBaseModel):
    subject: str = ""
    activity_type: str = "Other"

    date: Optional[date] = None

    description: Optional[str] = None

    status: str = "Open"

    customer_id: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    next_follow_up: Optional[date] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(CRMBaseModel):
    subject: Optional[str] = None
    activity_type: Optional[str] = None

    date: Optional[date] = None

    description: Optional[str] = None

    status: Optional[str] = None

    customer_id: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    next_follow_up: Optional[date] = None


class Activity(ActivityBase):
    id: Optional[str] = None
    activity_id: Optional[str] = None

    customer_name: Optional[str] = None

    created_at: Optional[datetime] = None


# ============================================================
# TASK
# ============================================================

class TaskBase(CRMBaseModel):
    title: str = ""

    subject: Optional[str] = None
    description: Optional[str] = None

    status: str = "Open"
    priority: str = "Medium"

    due_date: Optional[date] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(CRMBaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None

    status: Optional[str] = None
    priority: Optional[str] = None

    due_date: Optional[date] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None


class Task(TaskBase):
    id: Optional[str] = None
    task_id: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# PRODUCT
# ============================================================

class ProductBase(CRMBaseModel):
    product_name: Optional[str] = None
    name: Optional[str] = None

    product_code: Optional[str] = None
    code: Optional[str] = None
    part_number: Optional[str] = None

    brand: Optional[str] = None
    manufacturer: Optional[str] = None

    category: Optional[str] = None
    subcategory: Optional[str] = None

    description: Optional[str] = None

    specification: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None

    unit: Optional[str] = None

    price: Optional[float] = None
    cost: Optional[float] = None
    currency: Optional[str] = "IDR"

    status: Optional[str] = "Active"

    stock: Optional[float] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(CRMBaseModel):
    product_name: Optional[str] = None
    name: Optional[str] = None

    product_code: Optional[str] = None
    code: Optional[str] = None
    part_number: Optional[str] = None

    brand: Optional[str] = None
    manufacturer: Optional[str] = None

    category: Optional[str] = None
    subcategory: Optional[str] = None

    description: Optional[str] = None

    specification: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None

    unit: Optional[str] = None

    price: Optional[float] = None
    cost: Optional[float] = None
    currency: Optional[str] = None

    status: Optional[str] = None
    stock: Optional[float] = None


class Product(ProductBase):
    id: Optional[str] = None
    product_id: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# QUOTATION
# ============================================================

class QuotationItem(CRMBaseModel):
    """
    Individual quotation line item.

    Flexible fields are included so existing quotation payloads
    can be accepted without breaking the API.
    """

    product_id: Optional[str] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None

    description: Optional[str] = None
    part_number: Optional[str] = None

    brand: Optional[str] = None

    quantity: float = 1
    unit: Optional[str] = None

    unit_price: float = 0
    price: Optional[float] = None

    discount: float = 0
    discount_percent: float = 0

    subtotal: float = 0

    currency: Optional[str] = "IDR"

    notes: Optional[str] = None


class QuotationBase(CRMBaseModel):
    """
    Common quotation fields.
    """

    quotation_number: Optional[str] = None
    quotation_no: Optional[str] = None
    number: Optional[str] = None

    quotation_date: Optional[date] = None
    date: Optional[date] = None

    valid_until: Optional[date] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    contact_id: Optional[str] = None
    contact_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    subject: Optional[str] = None
    title: Optional[str] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    status: str = "Draft"

    currency: str = "IDR"

    items: List[QuotationItem] = Field(default_factory=list)

    subtotal: float = 0
    discount: float = 0
    discount_percent: float = 0

    tax: float = 0
    tax_percent: float = 0

    shipping_cost: float = 0
    other_cost: float = 0

    total: float = 0

    probability: Optional[float] = None

    project_name: Optional[str] = None
    project_id: Optional[str] = None


class QuotationCreate(QuotationBase):
    pass


class QuotationUpdate(CRMBaseModel):
    quotation_number: Optional[str] = None
    quotation_no: Optional[str] = None
    number: Optional[str] = None

    quotation_date: Optional[date] = None
    date: Optional[date] = None

    valid_until: Optional[date] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    contact_id: Optional[str] = None
    contact_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    subject: Optional[str] = None
    title: Optional[str] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    status: Optional[str] = None

    currency: Optional[str] = None

    items: Optional[List[QuotationItem]] = None

    subtotal: Optional[float] = None
    discount: Optional[float] = None
    discount_percent: Optional[float] = None

    tax: Optional[float] = None
    tax_percent: Optional[float] = None

    shipping_cost: Optional[float] = None
    other_cost: Optional[float] = None

    total: Optional[float] = None

    probability: Optional[float] = None

    project_name: Optional[str] = None
    project_id: Optional[str] = None


class Quotation(QuotationBase):
    id: Optional[str] = None
    quotation_id: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# AUTHENTICATION
# ============================================================

class LoginRequest(CRMBaseModel):
    email: str
    password: str


class LoginResponse(CRMBaseModel):
    success: bool = True

    message: Optional[str] = None

    token: Optional[str] = None
    access_token: Optional[str] = None

    user: Optional[Any] = None


class UserPublic(CRMBaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None

    email: Optional[str] = None

    name: Optional[str] = None
    full_name: Optional[str] = None

    role: Optional[str] = None

    status: Optional[str] = "Active"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(CRMBaseModel):
    email: str
    password: str

    name: Optional[str] = None
    full_name: Optional[str] = None

    role: str = "SALES"

    status: str = "Active"


class UserUpdate(CRMBaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

    name: Optional[str] = None
    full_name: Optional[str] = None

    role: Optional[str] = None

    status: Optional[str] = None


class User(CRMBaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None

    email: Optional[str] = None

    name: Optional[str] = None
    full_name: Optional[str] = None

    role: Optional[str] = None
    status: Optional[str] = "Active"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# FILE UPLOAD
# ============================================================

class UploadResponse(CRMBaseModel):
    success: bool = True

    message: Optional[str] = None

    filename: Optional[str] = None
    original_filename: Optional[str] = None

    file_url: Optional[str] = None
    url: Optional[str] = None

    path: Optional[str] = None

    content_type: Optional[str] = None

    size: Optional[int] = None


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

    open_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0

    open_activities: int = 0
    completed_activities: int = 0

    draft_quotations: int = 0
    sent_quotations: int = 0
    won_quotations: int = 0
    lost_quotations: int = 0

    total_sales: int = 0

    total_pipeline: float = 0
    total_revenue: float = 0
    total_quotation_value: float = 0

    customers_growth: float = 0
    activities_growth: float = 0
    tasks_growth: float = 0
    sales_growth: float = 0
    quotations_growth: float = 0


# ============================================================
# GENERIC API RESPONSE
# ============================================================

class APIResponse(CRMBaseModel):
    success: bool = True

    message: Optional[str] = None

    data: Optional[Any] = None


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Pagination
    "Paginated",

    # Customer
    "Customer",
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",

    # Contact
    "Contact",
    "ContactBase",
    "ContactCreate",
    "ContactUpdate",

    # Activity
    "Activity",
    "ActivityBase",
    "ActivityCreate",
    "ActivityUpdate",

    # Task
    "Task",
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",

    # Product
    "Product",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",

    # Quotation
    "Quotation",
    "QuotationBase",
    "QuotationCreate",
    "QuotationUpdate",
    "QuotationItem",

    # Authentication
    "LoginRequest",
    "LoginResponse",
    "User",
    "UserPublic",
    "UserCreate",
    "UserUpdate",

    # Upload
    "UploadResponse",

    # Dashboard
    "DashboardMetrics",

    # Generic
    "APIResponse",
]
