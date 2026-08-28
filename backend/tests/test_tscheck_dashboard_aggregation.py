"""API-bearing criterion: Real dashboard aggregation.

Verifies the /dashboard endpoint returns database-backed KPI aggregates matching
the seeded dataset scale (>=50 customers, quotations, purchase orders, activities,
and a six-stage pipeline breakdown).
"""


def _login(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def test_dashboard_returns_real_aggregates(client):
    cookies = _login(client)
    resp = client.get("/dashboard", cookies=cookies)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["total_customer"] >= 50, body
    assert body["total_quotation"] >= 30, body
    assert body["total_po"] >= 20, body
    assert body["activities"] >= 100, body
    assert isinstance(body["open_pipeline"], (int, float))
    assert isinstance(body["weighted_pipeline"], (int, float))

    stages = {row["stage"] for row in body["pipeline_by_stage"]}
    assert stages == {"Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"}
    for row in body["pipeline_by_stage"]:
        assert row["count"] >= 0
        assert isinstance(row["value"], (int, float))


def test_dashboard_requires_authentication(client):
    resp = client.get("/dashboard")
    assert resp.status_code in (401, 403), resp.text
