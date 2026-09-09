from __future__ import annotations

from typing import Any

from lib.db import db


SALES_ROLES = {"SALES", "SALES_MANAGER"}


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


async def get_sales_options() -> list[dict[str, str]]:
    """
    Single source of truth for Sales dropdowns across the CRM.

    Primary source is the Users collection. Active SALES and SALES_MANAGER
    users are always included. Legacy CRM records that already reference a
    user by sales_id or sales_name are also resolved back to that same user,
    so existing data remains selectable while the CRM is migrated toward
    sales_id-based relationships.
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
        if not user_id or not name:
            continue

        record = {"id": user_id, "name": name}
        by_id[user_id] = record
        by_name[_norm(name)] = record

    selected: dict[str, dict[str, str]] = {}

    # Canonical Sales users.
    for user in users:
        user_id = str(user.get("id") or "").strip()
        name = str(user.get("name") or "").strip()
        role = str(user.get("role") or "").strip().upper()
        status = str(user.get("status") or "").strip().upper()

        if (
            user_id
            and name
            and role in SALES_ROLES
            and status not in {"INACTIVE", "DISABLED"}
        ):
            selected[user_id] = {"id": user_id, "name": name}

    # Preserve existing assignments from all CRM modules by resolving them
    # to the same User record whenever possible.
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

            if record:
                selected[record["id"]] = record

    return sorted(
        selected.values(),
        key=lambda item: item["name"].casefold(),
    )
