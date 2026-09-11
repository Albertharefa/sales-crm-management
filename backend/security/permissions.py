from __future__ import annotations

from typing import Any

from fastapi import HTTPException

ROLES = {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}

# Permission names are deliberately stable. UI labels can change without
# changing the authorization contract used by the API.
PERMISSIONS: dict[str, set[str]] = {
    "SUPER_ADMIN": {
        "dashboard.view",
        "customers.view", "customers.create", "customers.edit", "customers.delete",
        "pipeline.view", "pipeline.create", "pipeline.edit", "pipeline.delete",
        "activities.view", "activities.create", "activities.edit", "activities.delete",
        "quotations.view", "quotations.create", "quotations.edit", "quotations.approve", "quotations.delete", "quotations.export",
        "purchase_orders.view", "purchase_orders.create", "purchase_orders.edit", "purchase_orders.delete", "purchase_orders.export",
        "order_monitoring.view", "order_monitoring.update",
        "sales_team.view", "sales_team.manage",
        "sales_targets.view", "sales_targets.manage",
        "users.view", "users.create", "users.edit", "users.delete", "users.reset_password",
        "products.view", "products.create", "products.edit", "products.delete",
        "audit_log.view",
        "ai.use", "uploads.use", "system.options",
    },
    "SALES_MANAGER": {
        "dashboard.view",
        "customers.view", "customers.create", "customers.edit",
        "pipeline.view", "pipeline.create", "pipeline.edit",
        "activities.view", "activities.create", "activities.edit",
        "quotations.view", "quotations.create", "quotations.edit", "quotations.approve", "quotations.export",
        "purchase_orders.view", "purchase_orders.create", "purchase_orders.edit", "purchase_orders.export",
        "order_monitoring.view", "order_monitoring.update",
        "sales_team.view",
        "sales_targets.view", "sales_targets.manage",
        "users.view",
        "products.view",
        "audit_log.view",
        "ai.use", "uploads.use", "system.options",
    },
    "SALES": {
        "dashboard.view",
        "customers.view", "customers.create", "customers.edit",
        "pipeline.view", "pipeline.create", "pipeline.edit",
        "activities.view", "activities.create", "activities.edit",
        "quotations.view", "quotations.create", "quotations.edit",
        "purchase_orders.view", "purchase_orders.create", "purchase_orders.edit",
        "order_monitoring.view", "order_monitoring.update",
        "products.view",
        "ai.use", "uploads.use", "system.options",
    },
}

MODULE_LABELS = {
    "dashboard": "Dashboard",
    "customers": "Customers",
    "pipeline": "Sales Pipeline",
    "activities": "Aktivitas",
    "quotations": "Quotations",
    "purchase_orders": "Purchase Orders",
    "order_monitoring": "Order Monitoring",
    "sales_team": "Sales Team",
    "sales_targets": "Target Sales",
    "users": "Users",
    "products": "Products",
    "audit_log": "Audit Log",
    "ai": "AI Assistant",
    "uploads": "Uploads",
    "system": "System",
}


def normalize_role(user: dict[str, Any]) -> str:
    return str(user.get("role") or "").strip().upper()


def has_permission(user: dict[str, Any], permission: str) -> bool:
    role = normalize_role(user)
    return permission in PERMISSIONS.get(role, set())


def require_permission(user: dict[str, Any], permission: str) -> None:
    if normalize_role(user) not in ROLES or not has_permission(user, permission):
        raise HTTPException(status_code=403, detail="Anda tidak memiliki izin untuk tindakan ini")


def permissions_for_role(role: str) -> list[str]:
    return sorted(PERMISSIONS.get(str(role or "").strip().upper(), set()))


def permission_policy(path: str, method: str) -> str | None:
    """Return the permission required by an API request, or None for public endpoints."""
    path = path.rstrip("/") or "/"
    method = method.upper()

    public_exact = {
        "/api/v1/login",
        "/api/v1/logout",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/health",
        "/health",
    }
    if path in public_exact or path.startswith("/assets/"):
        return None

    if not path.startswith("/api/v1"):
        return None

    route = path[len("/api/v1"):].rstrip("/") or "/"
    if route == "/me":
        return "system.options"
    if route.startswith("/docs") or route.startswith("/openapi"):
        return "__admin_only__"

    if route.startswith("/dashboard"):
        return "dashboard.view"
    if route.startswith("/customers"):
        return _crud_permission("customers", method)
    if route.startswith("/pipeline"):
        return _crud_permission("pipeline", method)
    if route.startswith("/activities"):
        return _crud_permission("activities", method)
    if route.startswith("/quotations"):
        if method == "GET":
            return "quotations.view"
        if route.endswith("/duplicate"):
            return "quotations.create"
        if route.endswith("/customer-po"):
            return "quotations.edit"
        if route.endswith("/pdf"):
            return "quotations.view"
        if method == "POST":
            return "quotations.create"
        if method in {"PUT", "PATCH"}:
            return "quotations.edit"
        if method == "DELETE":
            return "quotations.delete"
        return "quotations.view"
    if route.startswith("/purchase-orders"):
        if method == "GET":
            return "purchase_orders.view"
        if route.endswith("/status") and method in {"PATCH", "PUT", "POST"}:
            return "order_monitoring.update"
        if method == "POST":
            return "purchase_orders.create"
        if method in {"PUT", "PATCH"}:
            return "purchase_orders.edit"
        if method == "DELETE":
            return "purchase_orders.delete"
        return "purchase_orders.view"
    if route.startswith("/order-monitoring"):
        return "order_monitoring.view" if method == "GET" else "order_monitoring.update"
    if route.startswith("/products"):
        return _crud_permission("products", method)
    if route.startswith("/targets") or route.startswith("/sales-targets"):
        if method == "GET":
            return "sales_targets.view"
        return "sales_targets.manage"
    if route.startswith("/users"):
        if method == "GET":
            return "users.view"
        if route.endswith("/reset-password"):
            return "users.reset_password"
        if method == "POST":
            return "users.create"
        if method == "PUT" or method == "PATCH":
            return "users.edit"
        if method == "DELETE":
            return "users.delete"
        return "users.view"
    if route.startswith("/audit-logs"):
        return "audit_log.view"
    if route.startswith("/sales-team"):
        return "sales_team.view"
    if route.startswith("/ai"):
        return "ai.use"
    if route.startswith("/uploads"):
        return "uploads.use"
    if route.startswith("/options") or route.startswith("/exports"):
        return "system.options"

    return None


def _crud_permission(module: str, method: str) -> str:
    if method == "GET":
        return f"{module}.view"
    if method == "POST":
        return f"{module}.create"
    if method in {"PUT", "PATCH"}:
        return f"{module}.edit"
    if method == "DELETE":
        return f"{module}.delete"
    return f"{module}.view"


def role_matrix() -> list[dict[str, Any]]:
    modules = [
        ("Dashboard", "dashboard"),
        ("Customers", "customers"),
        ("Sales Pipeline", "pipeline"),
        ("Aktivitas", "activities"),
        ("Quotations", "quotations"),
        ("Purchase Orders", "purchase_orders"),
        ("Order Monitoring", "order_monitoring"),
        ("Sales Team", "sales_team"),
        ("Target Sales", "sales_targets"),
        ("Users", "users"),
        ("Products", "products"),
        ("Audit Log", "audit_log"),
    ]
    labels = {
        "SUPER_ADMIN": "Full Control",
        "SALES_MANAGER": "Team Scope",
        "SALES": "Self Scope",
    }
    result = []
    for label, module in modules:
        row: dict[str, Any] = {"module": label, "key": module}
        for role in ROLES:
            perms = PERMISSIONS[role]
            if module == "quotations" and "quotations.approve" in perms:
                text = "Kelola & Approve semua" if role == "SUPER_ADMIN" else "Kelola & Approve team"
            elif module in {"users", "sales_team", "sales_targets"}:
                text = {
                    "SUPER_ADMIN": "Kelola penuh" if module != "sales_team" else "Kelola penuh",
                    "SALES_MANAGER": "Kelola team" if module == "sales_targets" else "Lihat team",
                    "SALES": "Tidak ada akses" if module != "sales_targets" else "Lihat sendiri",
                }[role]
            elif module == "products":
                text = "Kelola penuh" if role == "SUPER_ADMIN" else "Lihat"
            elif module == "audit_log":
                text = "Lihat penuh" if role == "SUPER_ADMIN" else ("Lihat team" if role == "SALES_MANAGER" else "Tidak ada akses")
            elif role == "SUPER_ADMIN":
                text = "Kelola semua"
            elif role == "SALES_MANAGER":
                text = "Kelola team"
            else:
                text = "Kelola sendiri"
            if not any(p.startswith(f"{module}.") for p in perms):
                text = "Tidak ada akses"
            row[role.lower()] = text
        result.append(row)
    return result
