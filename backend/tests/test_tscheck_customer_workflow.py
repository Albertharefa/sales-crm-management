"""API-bearing criterion: Customer server-side workflow.

Verifies search + server pagination params are honored, required-field validation
rejects an incomplete payload, and creating a uniquely named customer makes it
retrievable via the search filter.
"""
import time


def _login(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def test_customer_search_pagination_and_create(client):
    cookies = _login(client)

    # server pagination
    page1 = client.get("/customers", params={"page": 1, "page_size": 5}, cookies=cookies)
    assert page1.status_code == 200, page1.text
    body1 = page1.json()
    assert len(body1["items"]) <= 5
    assert body1["total"] >= 50

    # required-field validation rejects incomplete payload
    invalid = client.post("/customers", json={}, cookies=cookies)
    assert invalid.status_code == 422, invalid.text

    # create a uniquely named customer
    unique_name = f"tscheck-customer-{int(time.time() * 1000)}"
    payload = {
        "name": unique_name,
        "industry": "Manufacturing",
        "city": "Jakarta",
        "phone": "+62 811 5550 1234",
        "email": f"{unique_name}@example.co.id",
        "pic_name": "QA Tester",
        "status": "Active",
        "address": "Jl. Testing No. 1",
    }
    created = client.post("/customers", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    created_body = created.json()
    assert created_body["name"] == unique_name

    # searchable via server-side search filter
    search_resp = client.get("/customers", params={"page": 1, "page_size": 10, "search": unique_name}, cookies=cookies)
    assert search_resp.status_code == 200, search_resp.text
    search_body = search_resp.json()
    names = [row["name"] for row in search_body["items"]]
    assert unique_name in names, search_body
