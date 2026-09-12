import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from lib.db import db


OPEN_STAGES = ["Lead", "Qualification", "Proposal", "Negotiation"]
REFERENCE_STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]
INACTIVE_QUOTATION_STATUSES = ["Accepted", "Rejected", "Expired", "Cancelled"]
INACTIVE_ORDER_STATUSES = ["Completed", "Cancelled"]
INACTIVE_ACTIVITY_STATUSES = ["Completed", "Cancelled"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


async def _visibility(user: dict, id_field: str = "sales_id", name_field: str = "sales_name") -> dict[str, Any]:
    if user.get("role") == "SUPER_ADMIN":
        return {}
    if user.get("role") == "SALES_MANAGER":
        reports = await db.users.find({"manager_id": user["id"]}, {"id": 1, "name": 1}).to_list(100)
        ids = [user["id"], *[item["id"] for item in reports]]
        names = [user["name"], *[item["name"] for item in reports]]
        return {"$or": [{id_field: {"$in": ids}}, {name_field: {"$in": names}}]}
    return {"$or": [{id_field: user["id"]}, {name_field: user["name"]}]}


def _number(field: str) -> dict:
    return {"$convert": {"input": f"${field}", "to": "double", "onError": 0, "onNull": 0}}


def _date(field: str) -> dict:
    return {"$convert": {"input": f"${field}", "to": "date", "onError": None, "onNull": None}}


def _json_safe(value: Any) -> Any:
    """Convert MongoDB/BSON values inside dashboard payloads to JSON-safe values."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value
    if isinstance(value, dict):
        return {_json_safe(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


async def _aggregate_one(collection: str, pipeline: list[dict]) -> dict:
    rows = await db[collection].aggregate(pipeline, allowDiskUse=False).to_list(1)
    return rows[0] if rows else {}


class DashboardService:
    async def get_metrics(self, user: dict, period: str | None = None, sales_id: str | None = None, stage: str | None = None, customer_id: str | None = None) -> dict[str, Any]:
        current = datetime.now(timezone.utc)
        stalled_before = current - timedelta(days=30)
        year_start = datetime(current.year, 1, 1, tzinfo=timezone.utc)
        next_year = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)

        period_days = {"30d": 30, "90d": 90, "365d": 365}.get(str(period or "").strip().lower())
        since = current - timedelta(days=period_days) if period_days else None
        visibility = await _visibility(user)

        def scoped(extra: dict[str, Any] | None = None) -> dict[str, Any]:
            clauses: list[dict[str, Any]] = [visibility]
            if sales_id:
                clauses.append({"sales_id": sales_id})
            if customer_id:
                clauses.append({"customer_id": customer_id})
            if extra:
                clauses.append(extra)
            return clauses[0] if len(clauses) == 1 else {"$and": clauses}

        customer_filter = scoped({"created_at": {"$gte": since}}) if since else scoped()
        contact_filter = scoped({"created_at": {"$gte": since}}) if since else scoped()
        lead_filter = scoped({"created_at": {"$gte": since}}) if since else scoped()
        opportunity_extra: dict[str, Any] = {}
        if stage and stage not in REFERENCE_STAGES:
            raise HTTPException(status_code=422, detail="Stage dashboard tidak valid")
        if stage:
            opportunity_extra["stage"] = stage
        if since:
            opportunity_extra["created_at"] = {"$gte": since}
        opportunity_filter = scoped(opportunity_extra)
        activity_filter = scoped({"date": {"$gte": since}}) if since else scoped()
        quotation_filter = scoped({"date": {"$gte": since}}) if since else scoped()
        order_filter = scoped({"date": {"$gte": since}}) if since else scoped()
        target_filter = scoped()

        opportunity_pipeline = [
            {"$match": opportunity_filter},
            {"$set": {"safe_value": _number("value"), "safe_probability": _number("probability"), "safe_created_at": _date("created_at"), "safe_target_close": _date("target_close"), "safe_stage": {"$ifNull": ["$stage", "Unknown"]}, "safe_sales_name": {"$ifNull": ["$sales_name", "Unassigned"]}}},
            {"$facet": {
                "totals": [{"$group": {"_id": None, "total_opportunities": {"$sum": 1}, "open_pipeline": {"$sum": {"$cond": [{"$in": ["$safe_stage", ["Won", "Lost"]]}, 0, "$safe_value"]}}, "weighted_pipeline": {"$sum": {"$cond": [{"$in": ["$safe_stage", ["Won", "Lost"]]}, 0, {"$multiply": ["$safe_value", {"$divide": ["$safe_probability", 100]}]}]}}, "won_value": {"$sum": {"$cond": [{"$eq": ["$safe_stage", "Won"]}, "$safe_value", 0]}}, "lost_value": {"$sum": {"$cond": [{"$eq": ["$safe_stage", "Lost"]}, "$safe_value", 0]}}, "won_count": {"$sum": {"$cond": [{"$eq": ["$safe_stage", "Won"]}, 1, 0]}}, "lost_count": {"$sum": {"$cond": [{"$eq": ["$safe_stage", "Lost"]}, 1, 0]}}}}],
                "by_stage": [{"$group": {"_id": "$safe_stage", "count": {"$sum": 1}, "value": {"$sum": "$safe_value"}}}, {"$sort": {"value": -1}}],
                "by_salesperson": [{"$match": {"safe_stage": {"$nin": ["Won", "Lost"]}}}, {"$group": {"_id": "$safe_sales_name", "count": {"$sum": 1}, "value": {"$sum": "$safe_value"}}}, {"$sort": {"value": -1}}, {"$limit": 10}],
                "risks": [{"$match": {"safe_stage": {"$nin": ["Won", "Lost"]}}}, {"$set": {"risk_reason": {"$switch": {"branches": [{"case": {"$and": [{"$ne": ["$safe_target_close", None]}, {"$lt": ["$safe_target_close", current]}]}, "then": "Expected close terlewat"}, {"case": {"$and": [{"$ne": ["$safe_created_at", None]}, {"$lt": ["$safe_created_at", stalled_before]}]}, "then": "Tidak bergerak >30 hari"}, {"case": {"$in": [{"$ifNull": ["$next_action", ""]}, ["", None]]}, "then": "Next action belum diisi"}], "default": None}}}}, {"$match": {"risk_reason": {"$ne": None}}}, {"$sort": {"safe_value": -1}}, {"$limit": 8}, {"$project": {"_id": 0, "id": 1, "opportunity_id": 1, "name": 1, "customer_name": {"$ifNull": ["$customer_name", "—"]}, "sales_name": 1, "value": "$safe_value", "stage": "$safe_stage", "expected_close": {"$cond": [{"$ne": ["$safe_target_close", None]}, {"$dateToString": {"date": "$safe_target_close", "format": "%Y-%m-%d"}}, None]}, "reason": "$risk_reason"}}],
            }},
        ]

        activity_pipeline = [
            {"$match": activity_filter},
            {"$set": {"safe_follow_up": _date("next_follow_up"), "safe_date": _date("date"), "safe_status": {"$ifNull": ["$status", "Open"]}}},
            {"$facet": {
                "totals": [{"$group": {"_id": None, "activities": {"$sum": 1}, "overdue_activities": {"$sum": {"$cond": [{"$and": [{"$not": [{"$in": ["$safe_status", INACTIVE_ACTIVITY_STATUSES]}]}, {"$ne": ["$safe_follow_up", None]}, {"$lt": ["$safe_follow_up", current]}]}, 1, 0]}}}}],
                "recent": [{"$sort": {"safe_date": -1, "created_at": -1}}, {"$limit": 8}, {"$project": {"_id": 0, "id": 1, "subject": 1, "activity_type": 1, "customer_name": 1, "sales_name": 1, "date": {"$cond": [{"$ne": ["$safe_date", None]}, {"$dateToString": {"date": "$safe_date", "format": "%Y-%m-%d"}}, None]}, "status": "$safe_status"}}],
            }},
        ]

        quotation_pipeline = [
            {"$match": quotation_filter},
            {"$set": {"safe_total": _number("grand_total"), "safe_status": {"$ifNull": ["$status", "Draft"]}}},
            {"$group": {"_id": None, "total_quotation": {"$sum": 1}, "active_quotations": {"$sum": {"$cond": [{"$in": ["$safe_status", INACTIVE_QUOTATION_STATUSES]}, 0, 1]}}, "quotation_value": {"$sum": {"$cond": [{"$in": ["$safe_status", INACTIVE_QUOTATION_STATUSES]}, 0, "$safe_total"]}}}},
        ]

        order_pipeline = [
            {"$match": order_filter},
            {"$set": {"safe_total": _number("total"), "safe_eta": _date("eta"), "safe_date": _date("date"), "safe_status": {"$ifNull": ["$status", "Received"]}}},
            {"$facet": {
                "totals": [{"$group": {"_id": None, "total_po": {"$sum": 1}, "po_value": {"$sum": "$safe_total"}, "completed_orders": {"$sum": {"$cond": [{"$eq": ["$safe_status", "Completed"]}, 1, 0]}}, "open_orders": {"$sum": {"$cond": [{"$in": ["$safe_status", INACTIVE_ORDER_STATUSES]}, 0, 1]}}, "overdue_orders": {"$sum": {"$cond": [{"$and": [{"$not": [{"$in": ["$safe_status", INACTIVE_ORDER_STATUSES]}]}, {"$ne": ["$safe_eta", None]}, {"$lt": ["$safe_eta", current]}]}, 1, 0]}}}}],
                "monthly": [{"$match": {"safe_date": {"$gte": year_start, "$lt": next_year}}}, {"$group": {"_id": {"$dateToString": {"date": "$safe_date", "format": "%Y-%m"}}, "actual": {"$sum": "$safe_total"}}}, {"$sort": {"_id": 1}}],
            }},
        ]

        target_pipeline = [
            {"$match": {**target_filter, "year": current.year}},
            {"$set": {"safe_target": _number("target")}},
            {"$facet": {"total": [{"$group": {"_id": None, "sales_target": {"$sum": "$safe_target"}}}], "monthly": [{"$group": {"_id": "$month", "target": {"$sum": "$safe_target"}}}, {"$sort": {"_id": 1}}]}},
        ]

        opportunity_result, activity_result, quotation_result, order_result, target_result, total_customer, total_contacts, total_leads = await asyncio.gather(
            _aggregate_one("opportunities", opportunity_pipeline),
            _aggregate_one("activities", activity_pipeline),
            _aggregate_one("quotations", quotation_pipeline),
            _aggregate_one("purchase_orders", order_pipeline),
            _aggregate_one("sales_targets", target_pipeline),
            db.customers.count_documents(customer_filter),
            db.contacts.count_documents(contact_filter),
            db.leads.count_documents(lead_filter),
        )

        opportunity_totals = (opportunity_result.get("totals") or [{}])[0]
        activity_totals = (activity_result.get("totals") or [{}])[0]
        quotation_totals = quotation_result or {}
        order_totals = (order_result.get("totals") or [{}])[0]
        target_totals = (target_result.get("total") or [{}])[0]
        won_count = int(opportunity_totals.get("won_count", 0))
        lost_count = int(opportunity_totals.get("lost_count", 0))
        closed_count = won_count + lost_count
        sales_target = float(target_totals.get("sales_target", 0))
        po_value = float(order_totals.get("po_value", 0))

        by_stage_rows = {row["_id"]: row for row in opportunity_result.get("by_stage", [])}
        extra_stages = [name for name in by_stage_rows if name not in REFERENCE_STAGES]
        pipeline_by_stage = [{"name": stage, "count": int(by_stage_rows.get(stage, {}).get("count", 0)), "value": float(by_stage_rows.get(stage, {}).get("value", 0))} for stage in [*REFERENCE_STAGES, *extra_stages]]
        pipeline_by_salesperson = [{"name": str(row["_id"]) if isinstance(row["_id"], ObjectId) else row["_id"], "count": int(row["count"]), "value": float(row["value"])} for row in opportunity_result.get("by_salesperson", [])]
        actual_by_month = {row["_id"]: float(row["actual"]) for row in order_result.get("monthly", []) if row.get("_id")}
        target_by_month = {int(row["_id"]): float(row["target"]) for row in target_result.get("monthly", []) if row.get("_id")}
        monthly_sales = [{"month": f"{current.year}-{month:02d}", "label": MONTH_LABELS[month - 1], "actual": actual_by_month.get(f"{current.year}-{month:02d}", 0), "target": target_by_month.get(month, 0)} for month in range(1, 13)]

        # Return a plain dictionary from the service boundary.
        # Keeping Pydantic out of this path prevents BSON ObjectId serialization
        # from failing before the router can safely normalize MongoDB values.
        return {
            "total_customer": total_customer,
            "total_contacts": total_contacts,
            "total_leads": total_leads,
            "total_opportunities": int(opportunity_totals.get("total_opportunities", 0)),
            "open_pipeline": float(opportunity_totals.get("open_pipeline", 0)),
            "weighted_pipeline": float(opportunity_totals.get("weighted_pipeline", 0)),
            "won_value": float(opportunity_totals.get("won_value", 0)),
            "lost_value": float(opportunity_totals.get("lost_value", 0)),
            "win_rate": (won_count / closed_count * 100) if closed_count else 0,
            "total_quotation": int(quotation_totals.get("total_quotation", 0)),
            "active_quotations": int(quotation_totals.get("active_quotations", 0)),
            "quotation_value": float(quotation_totals.get("quotation_value", 0)),
            "total_po": int(order_totals.get("total_po", 0)),
            "po_value": po_value,
            "open_orders": int(order_totals.get("open_orders", 0)),
            "completed_orders": int(order_totals.get("completed_orders", 0)),
            "overdue_orders": int(order_totals.get("overdue_orders", 0)),
            "activities": int(activity_totals.get("activities", 0)),
            "overdue_activities": int(activity_totals.get("overdue_activities", 0)),
            "sales_target": sales_target,
            "target_achievement": (po_value / sales_target * 100) if sales_target else 0,
            "pipeline_by_stage": _json_safe(pipeline_by_stage),
            "pipeline_by_salesperson": _json_safe(pipeline_by_salesperson),
            "monthly_sales_performance": _json_safe(monthly_sales),
            "recent_activities": _json_safe(activity_result.get("recent", [])),
            "deal_risks": _json_safe(opportunity_result.get("risks", [])),
            "generated_at": current,
        }
