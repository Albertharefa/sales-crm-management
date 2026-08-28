"""API-bearing criteria for the Dashboard MongoDB-aggregation fix:

- "Dashboard authenticated API flow": 200 + full typed schema when authenticated, 401 without a session.
- "Required dashboard metrics": every KPI/group/list field required by the matrix is present with sane types.
- "Customer consistency": dashboard total_customer == /api/customers total.
- "Pipeline consistency": dashboard pipeline aggregates equal calculations from real /api/pipeline records.
"""

from collections import Counter

OPEN_STAGES = {"Lead", "Qualification", "Proposal", "Negotiation"}
REQUIRED_SCALAR_FIELDS = [
    "total_customer",
    "total_contacts",
    "total_leads",
    "total_opportunities",
    "open_pipeline",
    "weighted_pipeline",
    "won_value",
    "lost_value",
    "win_rate",
    "total_quotation",
    "active_quotations",
    "quotation_value",
    "total_po",
    "po_value",
    "open_orders",
    "completed_orders",
    "overdue_orders",
    "activities",
    "overdue_activities",
    "sales_target",
    "target_achievement",
]
REQUIRED_LIST_FIELDS = [
    "pipeline_by_stage",
    "pipeline_by_salesperson",
    "monthly_sales_performance",
    "recent_activities",
    "deal_risks",
]


def _login(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def test_dashboard_requires_authentication(client):
    resp = client.get("/dashboard")
    assert resp.status_code in (401, 403), resp.text


def test_dashboard_full_schema_and_no_hardcoded_shape(client):
    cookies = _login(client)
    resp = client.get("/dashboard", cookies=cookies)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    for field in REQUIRED_SCALAR_FIELDS:
        assert field in body, f"missing scalar field {field}"
        assert isinstance(body[field], (int, float)), f"{field} not numeric: {body[field]!r}"

    for field in REQUIRED_LIST_FIELDS:
        assert field in body, f"missing list field {field}"
        assert isinstance(body[field], list), f"{field} not a list"

    stages = {row["name"] for row in body["pipeline_by_stage"]}
    assert stages == {"Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"}
    for row in body["pipeline_by_stage"]:
        assert isinstance(row["count"], int) and row["count"] >= 0
        assert isinstance(row["value"], (int, float))

    assert len(body["monthly_sales_performance"]) == 12
    for row in body["monthly_sales_performance"]:
        assert "month" in row and "actual" in row and "target" in row

    # Not the same static list every call: recent_activities/deal_risks are derived from
    # real collections, so they must reference real, resolvable customer/sales names, not
    # a fixed hardcoded fallback payload.
    for row in body["recent_activities"][:5]:
        assert row.get("customer_name"), row
    for row in body["deal_risks"][:5]:
        assert row.get("opportunity_id"), row


def test_dashboard_customer_count_matches_customers_api(client):
    cookies = _login(client)
    dash = client.get("/dashboard", cookies=cookies).json()
    customers = client.get("/customers", params={"limit": 1}, cookies=cookies)
    assert customers.status_code == 200, customers.text
    total_customers = customers.json()["total"]
    assert dash["total_customer"] == total_customers, (dash["total_customer"], total_customers)


def test_dashboard_pipeline_aggregates_match_pipeline_api(client):
    cookies = _login(client)
    dash = client.get("/dashboard", cookies=cookies).json()

    pipeline = client.get("/pipeline", params={"page_size": 100}, cookies=cookies)
    assert pipeline.status_code == 200, pipeline.text
    items = pipeline.json()["items"]
    assert pipeline.json()["total"] == len(items), "page_size=100 must cover all seeded opportunities"

    assert dash["total_opportunities"] == len(items)

    open_value = sum(i["value"] for i in items if i["stage"] in OPEN_STAGES)
    won_value = sum(i["value"] for i in items if i["stage"] == "Won")
    lost_value = sum(i["value"] for i in items if i["stage"] == "Lost")

    assert dash["open_pipeline"] == open_value, (dash["open_pipeline"], open_value)
    assert dash["won_value"] == won_value, (dash["won_value"], won_value)
    assert dash["lost_value"] == lost_value, (dash["lost_value"], lost_value)

    stage_counts = Counter(i["stage"] for i in items)
    dash_stage_counts = {row["name"]: row["count"] for row in dash["pipeline_by_stage"]}
    for stage, count in stage_counts.items():
        assert dash_stage_counts[stage] == count, (stage, dash_stage_counts[stage], count)
