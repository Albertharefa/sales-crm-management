from __future__ import annotations

from typing import Any

from lib.db import db


SALES_ROLES = {"SALES"}


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


async def get_sales_options() -> list[dict[str, str]]:
    """
    Single source of truth for Sales dropdowns across the CRM.

    The Sales master is sourced from active USERS whose role is SALES.
    SALES_MANAGER and SUPER_ADMIN are intentionally excluded because they
    are management/administration roles, not Sales owners.

    Existing CRM records are resolved back to the same SALES user when
    possible so legacy sales_name-only assignments remain selectable.
    """
    users = await db.users.find(
        {},
        {"_id": 0, "id": 1, "name": 1, "role": 1, "status": 1},
    ).sort("name", 1).to_list(1000)

    by_id: dict[str, dict[str, str]] = {}
    by_name: dict[str, dict[str, str]] = {}

    for user in users:
        user_id = str(user.get("id") or "").strip()
        name = str(user.get("name") or "").strip()
        role = str(user.get("role") or "").strip().upper()
        if not user_id or not name:
            continue

        record = {"id": user_id, "name": name, "role": role}
        by_id[user_id] = record
        by_name[_norm(name)] = record

    selected: dict[str, dict[str, str]] = {}

    # Canonical Sales master: active SALES users only.
    for user in users:
        user_id = str(user.get("id") or "").strip()
        name = str(user.get("name") or "").strip()
        role = str(user.get("role") or "").strip().upper()
        status = str(user.get("status") or "").strip().upper()

        if (
            user_id
            and name
            and role == "SALES"
            and status not in {"INACTIVE", "DISABLED"}
        ):
            selected[user_id] = {"id": user_id, "name": name, "role": role}

    # Preserve existing assignments only when they resolve to a real SALES
    # user. Management/admin users are never added to the Sales master.
    for collection_name in (
        "customers",
        "opportunities",
        "activities",
        "quotations",
        "purchase_orders",
    ):
        cursor = db[collection_name].find(
            {},
            {"_id": 0, "sales_id": 1, "sales_name": 1},
        )
        async for item in cursor:
            sales_id = str(item.get("sales_id") or "").strip()
            sales_name = str(item.get("sales_name") or "").strip()

            record = by_id.get(sales_id) if sales_id else None
            if record is None and sales_name:
                record = by_name.get(_norm(sales_name))

            if record and record.get("role") == "SALES":
                selected[record["id"]] = record

    return sorted(
        selected.values(),
        key=lambda item: item["name"].casefold(),
    )
