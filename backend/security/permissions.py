from __future__ import annotations
from typing import Any
from fastapi import HTTPException

ROLES = {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}

# Granular RBAC: ROLE x MODULE x ACTION.
# Data scope is enforced by the individual routers: SUPER_ADMIN=ALL,
# SALES_MANAGER=TEAM, SALES=SELF where applicable.
PERMISSIONS: dict[str, set[str]] = {
    "SUPER_ADMIN": {
        "dashboard.view",
        "customers.view", "customers.create", "customers.edit", "customers.delete", "customers.export",
        "pipeline.view", "pipeline.create", "pipeline.edit", "pipeline.delete", "pipeline.export",
        "activities.view", "activities.create", "activities.edit", "activities.delete", "activities.export",
        "quotations.view", "quotations.create", "quotations.edit", "quotations.approve", "quotations.delete", "quotations.export",
        "purchase_orders.view", "purchase_orders.create", "purchase_orders.edit", "purchase_orders.delete", "purchase_orders.export",
        "order_monitoring.view", "order_monitoring.update",
        "sales_team.view", "sales_team.manage", "sales_team.export",
        "sales_targets.view", "sales_targets.manage",
        "users.view", "users.create", "users.edit", "users.delete", "users.reset_password",
        "products.view", "products.create", "products.edit", "products.delete", "products.export",
        "audit_log.view",
        "ai.use", "uploads.use", "system.options", "integrity.audit",
    },
    "SALES_MANAGER": {
        "dashboard.view",
        "customers.view", "customers.create", "customers.edit", "customers.delete", "customers.export",
        "pipeline.view", "pipeline.create", "pipeline.edit", "pipeline.delete", "pipeline.export",
        "activities.view", "activities.create", "activities.edit", "activities.delete", "activities.export",
        "quotations.view", "quotations.create", "quotations.edit", "quotations.approve", "quotations.delete", "quotations.export",
        "purchase_orders.view", "purchase_orders.create", "purchase_orders.edit", "purchase_orders.delete", "purchase_orders.export",
        "order_monitoring.view", "order_monitoring.update",
        "sales_team.view", "sales_targets.view", "sales_targets.manage",
        "users.view",
        "products.view", "products.export",
        "audit_log.view",
        "ai.use", "uploads.use", "system.options",
    },
    "SALES": {
        "dashboard.view",
        "customers.view", "customers.create", "customers.edit", "customers.export",
        "pipeline.view", "pipeline.create", "pipeline.edit", "pipeline.export",
        "activities.view", "activities.create", "activities.edit", "activities.export",
        "quotations.view", "quotations.create", "quotations.edit", "quotations.export",
        "purchase_orders.view", "purchase_orders.create", "purchase_orders.edit", "purchase_orders.export",
        "order_monitoring.view", "order_monitoring.update",
        "sales_targets.view",
        "products.view", "products.export",
        "ai.use", "uploads.use", "system.options",
    },
}

# Human-readable policy used by documentation/UI integrations.
ROLE_SCOPE: dict[str, str] = {
    "SUPER_ADMIN": "ALL",
    "SALES_MANAGER": "TEAM",
    "SALES": "SELF",
}

MODULE_ACTIONS: dict[str, tuple[str, ...]] = {
    "dashboard": ("view",),
    "customers": ("view", "create", "edit", "delete", "export"),
    "pipeline": ("view", "create", "edit", "delete", "export"),
    "activities": ("view", "create", "edit", "delete", "export"),
    "quotations": ("view", "create", "edit", "approve", "delete", "export"),
    "purchase_orders": ("view", "create", "edit", "delete", "export"),
    "order_monitoring": ("view", "update"),
    "sales_team": ("view", "manage", "export"),
    "sales_targets": ("view", "manage"),
    "users": ("view", "create", "edit", "delete", "reset_password"),
    "products": ("view", "create", "edit", "delete", "export"),
    "audit_log": ("view",),
    "security": ("ai", "uploads", "system_options", "integrity_audit"),
}


def normalize_role(user: dict[str, Any]) -> str:
    return str(user.get("role") or "").strip().upper()


def has_permission(user: dict[str, Any], permission: str) -> bool:
    return permission in PERMISSIONS.get(normalize_role(user), set())


def require_permission(user: dict[str, Any], permission: str) -> None:
    if normalize_role(user) not in ROLES or not has_permission(user, permission):
        raise HTTPException(status_code=403, detail="Anda tidak memiliki izin untuk tindakan ini")


def permissions_for_role(role: str) -> list[str]:
    return sorted(PERMISSIONS.get(str(role or "").strip().upper(), set()))


def role_permission_matrix() -> list[dict[str, Any]]:
    """Return the canonical RBAC matrix without exposing user data."""
    rows: list[dict[str, Any]] = []
    for module, actions in MODULE_ACTIONS.items():
        for action in actions:
            permission = f"{module}.{action}"
            rows.append({
                "module": module,
                "action": action,
                "permission": permission,
                "super_admin": permission in PERMISSIONS["SUPER_ADMIN"],
                "sales_manager": permission in PERMISSIONS["SALES_MANAGER"],
                "sales": permission in PERMISSIONS["SALES"],
                "scope_super_admin": "ALL" if permission in PERMISSIONS["SUPER_ADMIN"] else "NONE",
                "scope_sales_manager": "TEAM" if permission in PERMISSIONS["SALES_MANAGER"] else "NONE",
                "scope_sales": "SELF" if permission in PERMISSIONS["SALES"] else "NONE",
            })
    return rows


def permission_policy(path: str, method: str) -> str | None:
    path = path.rstrip("/") or "/"
    method = method.upper()
    public_exact = {"/api/v1/login", "/api/v1/logout", "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password", "/api/v1/health", "/health"}
    if path in public_exact or path.startswith("/assets/"):
        return None
    if not path.startswith("/api/v1"):
        return None
    route = path[len("/api/v1"):].rstrip("/") or "/"
    if route in {"/me", "/session-info"}:
        return "system.options"
    if route.startswith("/docs") or route.startswith("/openapi"):
        return "__admin_only__"
    if route.startswith("/admin"): return "__admin_only__"
    if route.startswith("/integrity"): return "integrity.audit"
    if route.startswith("/dashboard"): return "dashboard.view"
    if route.startswith("/customers"): return _crud_permission("customers", method)
    if route.startswith("/pipeline"): return _crud_permission("pipeline", method)
    if route.startswith("/activities"): return _crud_permission("activities", method)
    if route.startswith("/quotations"):
        if method == "GET": return "quotations.view"
        if route.endswith("/duplicate"): return "quotations.create"
        if route.endswith("/customer-po"): return "quotations.edit"
        if route.endswith("/pdf"): return "quotations.view"
        if method == "POST": return "quotations.create"
        if method in {"PUT", "PATCH"}: return "quotations.edit"
        if method == "DELETE": return "quotations.delete"
        return "quotations.view"
    if route.startswith("/purchase-orders"):
        if method == "GET": return "purchase_orders.view"
        if route.endswith("/status") and method in {"PATCH", "PUT", "POST"}: return "order_monitoring.update"
        if method == "POST": return "purchase_orders.create"
        if method in {"PUT", "PATCH"}: return "purchase_orders.edit"
        if method == "DELETE": return "purchase_orders.delete"
        return "purchase_orders.view"
    if route.startswith("/order-monitoring"): return "order_monitoring.view" if method == "GET" else "order_monitoring.update"
    if route.startswith("/products"): return _crud_permission("products", method)
    if route.startswith("/targets") or route.startswith("/sales-targets"): return "sales_targets.view" if method == "GET" else "sales_targets.manage"
    if route.startswith("/users"):
        if method == "GET": return "users.view"
        if route.endswith("/reset-password"): return "users.reset_password"
        if method == "POST": return "users.create"
        if method in {"PUT", "PATCH"}: return "users.edit"
        if method == "DELETE": return "users.delete"
        return "users.view"
    if route.startswith("/audit-logs"): return "audit_log.view"
    if route.startswith("/sales-team"): return "sales_team.view"
    if route.startswith("/ai"): return "ai.use"
    if route.startswith("/uploads"): return "uploads.use"
    if route.startswith("/exports/"):
        export_module = route.split("/", 2)[2]
        module_map = {"customers": "customers", "pipeline": "pipeline", "activities": "activities", "quotations": "quotations", "purchase-orders": "purchase_orders", "products": "products", "sales-team": "sales_team"}
        module = module_map.get(export_module)
        if not module: return "system.options"
        export_permission = f"{module}.export"
        return export_permission if any(export_permission in perms for perms in PERMISSIONS.values()) else f"{module}.view"
    if route.startswith("/options"): return "system.options"
    return None


def _crud_permission(module: str, method: str) -> str:
    if method == "GET": return f"{module}.view"
    if method == "POST": return f"{module}.create"
    if method in {"PUT", "PATCH"}: return f"{module}.edit"
    if method == "DELETE": return f"{module}.delete"
    return f"{module}.view"


def role_matrix() -> list[dict[str, Any]]:
    """Backward-compatible summary matrix used by existing UI."""
    modules = [("Dashboard", "dashboard"), ("Customers", "customers"), ("Sales Pipeline", "pipeline"), ("Aktivitas", "activities"), ("Quotations", "quotations"), ("Purchase Orders", "purchase_orders"), ("Order Monitoring", "order_monitoring"), ("Sales Team", "sales_team"), ("Target Sales", "sales_targets"), ("Users", "users"), ("Products", "products"), ("Audit Log", "audit_log")]
    result = []
    for label, module in modules:
        row: dict[str, Any] = {"module": label, "key": module}
        for role in ("SUPER_ADMIN", "SALES_MANAGER", "SALES"):
            perms = PERMISSIONS[role]
            if module == "quotations" and "quotations.approve" in perms: text = "Kelola & Approve semua" if role == "SUPER_ADMIN" else "Kelola & Approve team"
            elif module == "sales_team": text = "Kelola penuh" if role == "SUPER_ADMIN" else ("Lihat team" if role == "SALES_MANAGER" else "Tidak ada akses")
            elif module == "sales_targets": text = "Kelola penuh" if role == "SUPER_ADMIN" else ("Kelola team" if role == "SALES_MANAGER" else "Lihat sendiri")
            elif module == "users": text = "Kelola penuh" if role == "SUPER_ADMIN" else ("Lihat team" if role == "SALES_MANAGER" else "Tidak ada akses")
            elif module == "products": text = "Kelola penuh" if role == "SUPER_ADMIN" else "Lihat"
            elif module == "audit_log": text = "Lihat penuh" if role == "SUPER_ADMIN" else ("Lihat team" if role == "SALES_MANAGER" else "Tidak ada akses")
            elif role == "SUPER_ADMIN": text = "Kelola semua"
            elif role == "SALES_MANAGER": text = "Kelola team"
            else: text = "Kelola sendiri"
            if not any(p.startswith(f"{module}.") for p in perms): text = "Tidak ada akses"
            row[role.lower()] = text
        result.append(row)
    return result
