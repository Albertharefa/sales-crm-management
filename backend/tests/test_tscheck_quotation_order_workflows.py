"""API-bearing criterion: Quotation and order workflows.

Verifies quotations list real data, a quotation can be created with server-
calculated totals plus a PDF is downloadable; purchase orders allow valid
creation; and order monitoring allows a six-stage status update.
"""
import time


VALID_ORDER_STAGES = ["Received", "Processing", "Indent", "Ready Stock", "Delivery", "Completed"]


def _login(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def _seed_options(client, cookies):
    resp = client.get("/options", cookies=cookies)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["customers"] and body["products"]
    return body["customers"][0]["id"], body["products"][0]["id"]


def test_quotations_list_create_with_server_totals_and_pdf(client):
    cookies = _login(client)

    listing = client.get("/quotations", params={"page": 1, "page_size": 10}, cookies=cookies)
    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] >= 25

    customer_id, product_id = _seed_options(client, cookies)
    payload = {
        "customer_id": customer_id,
        "date": "2026-09-01",
        "payment_term": "NET 30",
        "items": [
            {"product_id": product_id, "description": f"tscheck-quotation-item-{int(time.time() * 1000)}",
             "quantity": 2, "unit_price": 1000000, "discount": 0, "tax": 11}
        ],
    }
    created = client.post("/quotations", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    body = created.json()
    # server-calculated totals: subtotal = qty*price, tax applied on top
    assert body["subtotal"] == 2000000
    assert body["grand_total"] > body["subtotal"]

    pdf = client.get(f"/quotations/{body['id']}/pdf", cookies=cookies)
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers.get("content-type", "").startswith("application/pdf")


def test_purchase_order_create_and_order_monitoring_status_update(client):
    cookies = _login(client)
    customer_id, product_id = _seed_options(client, cookies)

    po_number = f"tscheck-po-{int(time.time() * 1000)}"
    payload = {
        "po_number": po_number,
        "customer_id": customer_id,
        "date": "2026-09-01",
        "status": "Received",
        "items": [{"product_id": product_id, "description": "QA item", "quantity": 1, "unit_price": 500000}],
    }
    created = client.post("/purchase-orders", json=payload, cookies=cookies)
    assert created.status_code in (200, 201), created.text
    order = created.json()
    assert order["po_number"] == po_number
    assert order["total"] == 500000

    monitoring = client.get("/purchase-orders/monitoring", params={"page": 1, "page_size": 5}, cookies=cookies)
    assert monitoring.status_code == 200, monitoring.text
    assert monitoring.json()["total"] >= 15

    # six-stage status update path
    next_stage = VALID_ORDER_STAGES[1]
    update = client.patch(f"/purchase-orders/{order['id']}/status", params={"status": next_stage}, cookies=cookies)
    assert update.status_code == 200, update.text
    assert update.json()["status"] == next_stage
