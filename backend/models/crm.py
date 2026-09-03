from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# BASE CONFIG
# ============================================================

class CRMBaseModel(BaseModel):
    """
    Base model untuk seluruh CRM.
    Extra fields diperbolehkan agar model tetap kompatibel
    dengan data MongoDB yang mungkin memiliki field tambahan.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


# ============================================================
# PAGINATION
# ============================================================

class Paginated(CRMBaseModel):
    items: list[Any] = Field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0


# ============================================================
# CUSTOMER
# ============================================================

class Customer(CRMBaseModel):
    id: str
    name: str

    customer_id: Optional[str] = None

    company: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: Optional[str] = "Active"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None

    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class CustomerCreate(CRMBaseModel):
    name: str

    customer_id: Optional[str] = None

    company: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: Optional[str] = "Active"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None


class CustomerUpdate(CRMBaseModel):
    name: Optional[str] = None
    customer_id: Optional[str] = None

    company: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    notes: Optional[str] = None


# ============================================================
# CUSTOMER CONTACT
# ============================================================

class Contact(CRMBaseModel):
    id: str

    customer_id: str

    name: str
    position: Optional[str] = None
    department: Optional[str] = None

    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    notes: Optional[str] = None

    status: Optional[str] = "Active"

    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class ContactCreate(CRMBaseModel):
    name: str

    position: Optional[str] = None
    department: Optional[str] = None

    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    notes: Optional[str] = None

    status: Optional[str] = "Active"


class ContactUpdate(CRMBaseModel):
    name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    notes: Optional[str] = None

    status: Optional[str] = None


# ============================================================
# ACTIVITY
# ============================================================

class Activity(CRMBaseModel):
    id: str

    activity_id: Optional[str] = None

    subject: str
    activity_type: str

    date: Optional[Any] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    next_follow_up: Optional[Any] = None

    status: str = "Open"

    description: Optional[str] = None

    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class ActivityCreate(CRMBaseModel):
    customer_id: Optional[str] = None

    subject: str
    activity_type: str

    date: Optional[Any] = None

    description: Optional[str] = None

    status: str = "Open"

    next_follow_up: Optional[Any] = None


# ============================================================
# TASK
# ============================================================

class Task(CRMBaseModel):
    id: str

    task_id: Optional[str] = None

    title: Optional[str] = None
    subject: Optional[str] = None

    description: Optional[str] = None

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    due_date: Optional[Any] = None

    priority: Optional[str] = "Medium"

    status: str = "Open"

    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class TaskCreate(CRMBaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None

    description: Optional[str] = None

    customer_id: Optional[str] = None

    due_date: Optional[Any] = None

    priority: Optional[str] = "Medium"

    status: str = "Open"


class TaskUpdate(CRMBaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None

    description: Optional[str] = None

    customer_id: Optional[str] = None

    due_date: Optional[Any] = None

    priority: Optional[str] = None

    status: Optional[str] = None


# ============================================================
# AUTHENTICATION
# ============================================================

class LoginRequest(CRMBaseModel):
    email: str
    password: str


class UserPublic(CRMBaseModel):
    id: str

    email: str
    name: str

    role: str = "SALES"

    is_active: bool = True

    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class UserCreate(CRMBaseModel):
    email: str
    password: str

    name: str

    role: str = "SALES"

    is_active: bool = True


class UserUpdate(CRMBaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

    name: Optional[str] = None

    role: Optional[str] = None

    is_active: Optional[bool] = None


class LoginResponse(CRMBaseModel):
    access_token: str
    token_type: str = "bearer"

    user: Optional[UserPublic] = None


# ============================================================
# DASHBOARD
# ============================================================

class DashboardMetrics(CRMBaseModel):
    total_customers: int = 0
    total_contacts: int = 0
    total_activities: int = 0
    total_tasks: int = 0

    open_tasks: int = 0
    completed_tasks: int = 0

    open_activities: int = 0
    completed_activities: int = 0

    overdue_tasks: int = 0

    total_sales: int = 0

    pipeline_value: float = 0.0
    won_value: float = 0.0
    lost_value: float = 0.0


# ============================================================
# UPLOAD
# ============================================================

class UploadResponse(CRMBaseModel):
    success: bool = True

    filename: Optional[str] = None
    original_filename: Optional[str] = None

    file_url: Optional[str] = None
    url: Optional[str] = None

    path: Optional[str] = None

    content_type: Optional[str] = None

    size: Optional[int] = None

    message: Optional[str] = None

    created_at: Optional[Any] = None


# ============================================================
# GENERIC API RESPONSE
# ============================================================

class MessageResponse(CRMBaseModel):
    success: bool = True
    message: str


class DeleteResponse(CRMBaseModel):
    success: bool = True
    message: str


# ============================================================
# HEALTH
# ============================================================

class HealthResponse(CRMBaseModel):
    status: str = "ok"
    database: Optional[str] = None
    version: Optional[str] = None
