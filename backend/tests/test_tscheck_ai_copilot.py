"""API-bearing criteria: AI access control, streaming, audit trail.

Verifies /api/ai endpoints reject unauthenticated requests, that context options
are role-scoped, that an authenticated GPT-5.4 streaming chat produces real
incremental content plus an audit record, and that no secret/API key leaks into
API responses.
"""
import os
import time

import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API_URL = f"{BACKEND_URL}/api"
LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


def _login(client, email="admin@crm.co.id", password="Password123"):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.cookies


def test_ai_endpoints_reject_unauthenticated(client):
    resp = client.get("/ai/context-options", params={"context_type": "customer"})
    assert resp.status_code in (401, 403), resp.text

    resp2 = client.post(
        "/ai/chat/stream",
        json={"prompt": "tscheck unauthenticated prompt", "context_type": "dashboard"},
    )
    assert resp2.status_code in (401, 403), resp2.text


def test_ai_context_options_role_scoped(client):
    admin_cookies = _login(client, "admin@crm.co.id", "Password123")
    admin_options = client.get("/ai/context-options", params={"context_type": "customer"}, cookies=admin_cookies)
    assert admin_options.status_code == 200, admin_options.text
    admin_list = admin_options.json()
    assert len(admin_list) > 0
    assert "id" in admin_list[0] and "name" in admin_list[0]

    sales_cookies = _login(client, "sales@crm.co.id", "Password123")
    sales_options = client.get("/ai/context-options", params={"context_type": "customer"}, cookies=sales_cookies)
    assert sales_options.status_code == 200, sales_options.text
    sales_list = sales_options.json()
    # A single SALES rep must never see more records than SUPER_ADMIN (role-scoped visibility).
    assert len(sales_list) <= len(admin_list)


def test_ai_chat_stream_authenticated_and_audited(client):
    cookies = _login(client)
    unique_prompt = f"tscheck-ai-{int(time.time() * 1000)}: ringkas pipeline dalam 1 kalimat singkat"

    events = []
    raw_text_chunks = []
    with httpx.Client(base_url=API_URL, timeout=60.0, cookies=cookies) as stream_client:
        with stream_client.stream(
            "POST",
            "/ai/chat/stream",
            json={"prompt": unique_prompt, "capability": "report_analyst", "context_type": "dashboard"},
        ) as resp:
            assert resp.status_code == 200, resp.text
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                raw_text_chunks.append(line)
                import json as _json
                events.append(_json.loads(line[len("data: "):]))

    assert len(events) > 0
    meta_events = [e for e in events if e.get("type") == "meta"]
    assert meta_events, events
    assert meta_events[0]["model"] == "gpt-5.4"
    conversation_id = meta_events[0]["conversation_id"]
    assistant_message_id = meta_events[0]["assistant_message_id"]

    delta_events = [e for e in events if e.get("type") == "delta"]
    done_events = [e for e in events if e.get("type") == "done"]
    error_events = [e for e in events if e.get("type") == "error"]
    assert not error_events, error_events
    assert done_events, events
    full_answer = "".join(e.get("content", "") for e in delta_events)
    assert len(full_answer.strip()) > 0, "expected real incremental GPT-5.4 content"

    # No secret/API key leakage anywhere in the raw SSE payload.
    combined = "\n".join(raw_text_chunks)
    assert LLM_KEY == "" or LLM_KEY not in combined
    assert "EMERGENT_LLM_KEY" not in combined

    # Audit trail: a "Generate" action against module "AI Copilot" must exist.
    audit_resp = client.get("/audit-logs", params={"page": 1, "page_size": 20}, cookies=cookies)
    assert audit_resp.status_code == 200, audit_resp.text
    rows = audit_resp.json()["items"]
    assert any(r.get("module") == "AI Copilot" and r.get("record_id") == assistant_message_id for r in rows), rows

    # History persistence: reopening the conversation restores stored messages.
    history_resp = client.get(f"/ai/conversations/{conversation_id}", cookies=cookies)
    assert history_resp.status_code == 200, history_resp.text
    history = history_resp.json()
    assert any(m["role"] == "user" and m["content"] == unique_prompt for m in history["messages"])
    assert any(m["role"] == "assistant" and m["id"] == assistant_message_id for m in history["messages"])


def test_ai_notes_confirm_requires_valid_draft_and_explicit_save(client):
    cookies = _login(client)
    # An unknown conversation/message pair must be rejected (nothing auto-saved).
    bogus_resp = client.post(
        "/ai/notes/confirm",
        json={"conversation_id": "tscheck-bogus-conv", "message_id": "tscheck-bogus-msg", "target_type": "dashboard"},
        cookies=cookies,
    )
    assert bogus_resp.status_code == 404, bogus_resp.text

    # Now do a real generate + confirm-save happy path.
    unique_prompt = f"tscheck-ai-save-{int(time.time() * 1000)}: sebutkan 1 risiko pipeline"
    events = []
    with httpx.Client(base_url=API_URL, timeout=60.0, cookies=cookies) as stream_client:
        with stream_client.stream(
            "POST",
            "/ai/chat/stream",
            json={"prompt": unique_prompt, "capability": "sales_copilot", "context_type": "dashboard"},
        ) as resp:
            assert resp.status_code == 200, resp.text
            for line in resp.iter_lines():
                if line and line.startswith("data: "):
                    import json as _json
                    events.append(_json.loads(line[len("data: "):]))
    meta = next(e for e in events if e["type"] == "meta")
    conversation_id = meta["conversation_id"]
    assistant_message_id = meta["assistant_message_id"]
    full_answer = "".join(e.get("content", "") for e in events if e["type"] == "delta")
    assert len(full_answer.strip()) > 0

    save_resp = client.post(
        "/ai/notes/confirm",
        json={"conversation_id": conversation_id, "message_id": assistant_message_id, "target_type": "dashboard", "title": "tscheck AI note"},
        cookies=cookies,
    )
    assert save_resp.status_code == 200, save_resp.text
    saved = save_resp.json()
    assert saved["content"] == full_answer
    assert saved["target_type"] == "dashboard"

    audit_resp = client.get("/audit-logs", params={"page": 1, "page_size": 20}, cookies=cookies)
    rows = audit_resp.json()["items"]
    assert any(r.get("module") == "AI Copilot" and r.get("action") == "Confirm Save" and r.get("record_id") == saved["id"] for r in rows)
