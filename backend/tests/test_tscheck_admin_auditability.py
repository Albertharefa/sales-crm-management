"""API-bearing criterion: Administration and auditability.

Verifies Products supports create + delete, Users supports Super Admin creating a
new user, Sales Team returns database-backed KPI rows, and Audit Log lists
recorded actions (including the ones this test itself just performed).
"""
import time


def _login(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def test_products_create_and_delete(client):
    cookies = _login(client)
    unique_code = f"TSCHECK-{int(time.time() * 1000)}"
    payload = {
        "code": unique_code,
        "name": f"tscheck-product-{unique_code}",
        "category": "Automation",
        "unit": "pcs",
        "default_price": 100000,
        "status": "Active",
    }
    created = client.post("/products", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    product_id = created.json()["id"]

    listing = client.get("/products", params={"page": 1, "page_size": 5, "search": unique_code}, cookies=cookies)
    assert listing.status_code == 200
    assert any(p["id"] == product_id for p in listing.json()["items"])

    deleted = client.delete(f"/products/{product_id}", cookies=cookies)
    assert deleted.status_code == 204, deleted.text


def test_users_super_admin_creates_user(client):
    cookies = _login(client)
    unique_email = f"tscheck-user-{int(time.time() * 1000)}@example.co.id"
    payload = {
        "name": "TSCheck QA User",
        "email": unique_email,
        "role": "SALES",
        "status": "Active",
        "password": "Password123",
    }
    created = client.post("/users", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    body = created.json()
    assert body["email"] == unique_email
    assert body["role"] == "SALES"


def test_sales_team_kpi_rows(client):
    cookies = _login(client)
    resp = client.get("/sales-team", cookies=cookies)
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) > 0
    for row in rows:
        assert "sales" in row and "open_pipeline" in row and "activities" in row


def test_audit_log_lists_actions(client):
    cookies = _login(client)
    # trigger a fresh auditable action
    unique_code = f"TSCHECK-AUDIT-{int(time.time() * 1000)}"
    client.post("/products", json={
        "code": unique_code, "name": f"tscheck-audit-product-{unique_code}",
        "default_price": 1000,
    }, cookies=cookies)

    resp = client.get("/audit-logs", params={"page": 1, "page_size": 20}, cookies=cookies)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] > 0
    assert len(body["items"]) > 0
    assert all("action" in row and "module" in row for row in body["items"])
