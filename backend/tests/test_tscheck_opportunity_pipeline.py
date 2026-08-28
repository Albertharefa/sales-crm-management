"""API-bearing criterion: Opportunity pipeline.

Verifies /pipeline lists real opportunities with six stages available, the kanban
endpoint groups by stage, and a valid opportunity can be created linked to a
seeded customer with weighted-value inputs accepted.
"""
import time


def _login(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def _seed_customer_id(client, cookies):
    resp = client.get("/options", cookies=cookies)
    assert resp.status_code == 200, resp.text
    customers = resp.json()["customers"]
    assert customers, "expected at least one seeded customer for options"
    return customers[0]["id"]


def test_pipeline_lists_real_opportunities_and_kanban_stages(client):
    cookies = _login(client)

    table = client.get("/pipeline", params={"page": 1, "page_size": 10}, cookies=cookies)
    assert table.status_code == 200, table.text
    body = table.json()
    assert body["total"] >= 40
    assert len(body["items"]) > 0

    kanban = client.get("/pipeline/kanban", cookies=cookies)
    assert kanban.status_code == 200, kanban.text
    kanban_body = kanban.json()
    stage_names = {row["stage"] for row in kanban_body} if isinstance(kanban_body, list) else set(kanban_body.keys())
    expected_stages = {"Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"}
    assert expected_stages.issubset(stage_names), kanban_body


def test_create_opportunity_linked_to_seeded_customer(client):
    cookies = _login(client)
    customer_id = _seed_customer_id(client, cookies)

    unique_name = f"tscheck-opportunity-{int(time.time() * 1000)}"
    payload = {
        "name": unique_name,
        "customer_id": customer_id,
        "value": 15000000,
        "probability": 40,
        "stage": "Qualification",
        "next_action": "Send proposal",
    }
    created = client.post("/pipeline", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    body = created.json()
    assert body["name"] == unique_name
    assert body["customer_id"] == customer_id
    assert body["stage"] == "Qualification"

    # invalid payload (missing required customer_id) is rejected
    invalid = client.post("/pipeline", json={"name": "x", "value": 100}, cookies=cookies)
    assert invalid.status_code == 422, invalid.text
