from security.permissions import has_permission, permission_policy, permissions_for_role


def test_role_matrix_core_permissions():
    admin = {"role": "SUPER_ADMIN"}
    manager = {"role": "SALES_MANAGER"}
    sales = {"role": "SALES"}

    assert has_permission(admin, "users.delete")
    assert has_permission(manager, "quotations.approve")
    assert has_permission(manager, "users.view")
    assert not has_permission(manager, "users.delete")
    assert not has_permission(sales, "users.view")
    assert not has_permission(sales, "quotations.approve")
    assert has_permission(sales, "quotations.edit")


def test_api_permission_policy():
    assert permission_policy("/api/v1/customers", "GET") == "customers.view"
    assert permission_policy("/api/v1/customers/abc", "DELETE") == "customers.delete"
    assert permission_policy("/api/v1/quotations/abc", "PUT") == "quotations.edit"
    assert permission_policy("/api/v1/purchase-orders/abc/status", "PATCH") == "order_monitoring.update"
    assert permission_policy("/api/v1/users/abc/reset-password", "POST") == "users.reset_password"
    assert permission_policy("/api/v1/exports/sales-team", "GET") == "sales_team.view"
    assert permission_policy("/api/v1/auth/forgot-password", "POST") is None


def test_permission_list_is_stable_and_sorted():
    permissions = permissions_for_role("SALES")
    assert permissions == sorted(permissions)
    assert "dashboard.view" in permissions
    assert "system.options" in permissions
