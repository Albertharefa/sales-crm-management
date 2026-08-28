"""API-bearing criterion: Activities and tasks.

Verifies /activities lists real seeded activities, a customer-linked activity can
be created, /activities/tasks lists real tasks, and a pending task can be marked
Completed.
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
    assert customers
    return customers[0]["id"]


def test_activities_list_and_create_customer_linked(client):
    cookies = _login(client)

    listing = client.get("/activities", params={"page": 1, "page_size": 10}, cookies=cookies)
    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] >= 50

    customer_id = _seed_customer_id(client, cookies)
    unique_subject = f"tscheck-activity-{int(time.time() * 1000)}"
    payload = {
        "subject": unique_subject,
        "activity_type": "Call",
        "date": "2026-09-01",
        "customer_id": customer_id,
        "status": "Open",
        "description": "Created by backend test",
    }
    created = client.post("/activities", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    body = created.json()
    assert body["subject"] == unique_subject
    assert body["customer_id"] == customer_id


def test_tasks_list_and_complete_pending_task(client):
    cookies = _login(client)

    listing = client.get("/activities/tasks", params={"page": 1, "page_size": 10}, cookies=cookies)
    assert listing.status_code == 200, listing.text
    body = listing.json()
    assert body["total"] >= 40

    pending = next((t for t in body["items"] if t["status"] == "Pending"), None)
    if pending is None:
        # search further pages for a pending task
        for page in range(2, 6):
            more = client.get("/activities/tasks", params={"page": page, "page_size": 10}, cookies=cookies)
            assert more.status_code == 200
            pending = next((t for t in more.json()["items"] if t["status"] == "Pending"), None)
            if pending:
                break
    assert pending is not None, "expected at least one seeded Pending task"

    update = client.patch(f"/activities/tasks/{pending['id']}", params={"status": "Completed"}, cookies=cookies)
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "Completed"
