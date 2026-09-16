import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException

from lib.db import db

OPEN_STAGES = ["Lead", "Qualification", "Proposal", "Negotiation"]
REFERENCE_STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]
INACTIVE_QUOTATION_STATUSES = ["Accepted", "Rejected", "Expired", "Cancelled"]
INACTIVE_ORDER_STATUSES = ["Completed", "Cancelled"]
INACTIVE_ACTIVITY_STATUSES = ["Completed", "Cancelled"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _number(field: str) -> dict:
    return {"$convert": {"input": f"${field}", "to": "double", "onError": 0, "onNull": 0}}


def _date(field: str) -> dict:
    return {"$convert": {"input": f"${field}", "to": "date", "onError": None, "onNull": None}}


async def _visibility(user: dict) -> dict[str, Any]:
    role = str(user.get("role") or "").strip().upper()
    if role == "SUPER_ADMIN":
        return {}
    if role == "SALES_MANAGER":
        reports = await db.users.find({"manager_id": user["id"]}, {"id": 1, "name": 1}).to_list(100)
        ids = [user["id"], *[item["id"] for item in reports]]
        names = [user["name"], *[item["name"] for item in reports]]
        return {"$or": [{"sales_id": {"$in": ids}}, {"sales_name": {"$in": names}}]}
    return {"$or": [{"sales_id": user["id"]}, {"sales_name": user["name"]}]}


async def _one(collection: str, pipeline: list[dict]) -> dict:
    rows = await db[collection].aggregate(pipeline, allowDiskUse=True).to_list(1)
    return rows[0] if rows else {}


async def _many(collection: str, pipeline: list[dict]) -> list[dict]:
    return await db[collection].aggregate(pipeline, allowDiskUse=True).to_list(100)


class FastDashboardService:
    async def get_metrics(
        self,
        user: dict,
        period: str | None = None,
        sales_id: str | None = None,
        stage: str | None = None,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        current = datetime.now(timezone.utc)
        stalled_before = current - timedelta(days=30)
        period_days = {"30d": 30, "90d": 90, "365d": 365}.get(str(period or "").strip().lower())
        since = current - timedelta(days=period_days) if period_days else None
        visibility = await _visibility(user)

        if stage and stage not in REFERENCE_STAGES:
            raise HTTPException(status_code=422, detail="Stage dashboard tidak valid")

        def scoped(extra: dict[str, Any] | None = None) -> dict[str, Any]:
            clauses: list[dict[str, Any]] = []
            if visibility:
                clauses.append(visibility)
            if sales_id:
                clauses.append({"sales_id": sales_id})
            if customer_id:
                clauses.append({"customer_id": customer_id})
            if extra:
                clauses.append(extra)
            if not clauses:
                return {}
            return clauses[0] if len(clauses) == 1 else {"$and": clauses}

        customer_filter = scoped({"created_at": {"$gte": since}}) if since else scoped()
        contact_filter = scoped({"created_at": {"$gte": since}}) if since else scoped()
        lead_filter = scoped({"created_at": {"$gte": since}}) if since else scoped()

        opportunity_extra: dict[str, Any] = {}
        if stage:
            opportunity_extra["stage"] = stage
        if since:
            opportunity_extra["created_at"] = {"$gte": since}
        opportunity_filter = scoped(opportunity_extra)
        activity_filter = scoped({"date": {"$gte": since}}) if since else scoped()
        quotation_filter = scoped({"date": {"$gte": since}}) if since else scoped()
        order_filter = scoped({"date": {"$gte": since}}) if since else scoped()
        target_filter = scoped()

        opportunity_summary = [
            {"$match": opportunity_filter},
            {"$project": {
                "stage": {"$ifNull": ["$stage", "Unknown"]},
                "sales_name": {"$ifNull": ["$sales_name", "Unassigned"]},
                "value": _number("value"),
                "probability": _number("probability"),
            }},
            {"$group": {
                "_id": {"stage": "$stage", "sales_name": "$sales_name"},
                "count": {"$sum": 1},
                "value": {"$sum": "$value"},
                "weighted": {"$sum": {"$cond": [{"$in": ["$stage", ["Won", "Lost"]]}, 0, {"$multiply": ["$value", {"$divide": ["$probability", 100]}]}]}},
            }},
        ]

        activity_summary = [
            {"$match": activity_filter},
            {"$project": {"status": {"$ifNull": ["$status", "Open"]}, "next_follow_up": _date("next_follow_up"), "date": _date("date"), "created_at": 1}},
            {"$group": {"_id": None, "activities": {"$sum": 1}, "overdue_activities": {"$sum": {"$cond": [{"$and": [{"$not": [{"$in": ["$status", INACTIVE_ACTIVITY_STATUSES]}]}, {"$ne": ["$next_follow_up", None]}, {"$lt": ["$next_follow_up", current]}]}, 1, 0]}}}},
        ]

        quotation_summary = [
            {"$match": quotation_filter},
            {"$project": {"status": {"$ifNull": ["$status", "Draft"]}, "total": _number("grand_total")}},
            {"$group": {"_id": None, "total_quotation": {"$sum": 1}, "active_quotations": {"$sum": {"$cond": [{"$in": ["$status", INACTIVE_QUOTATION_STATUSES]}, 0, 1]}}, "quotation_value": {"$sum": {"$cond": [{"$in": ["$status", INACTIVE_QUOTATION_STATUSES]}, 0, "$total"]}}}},
        ]

        order_summary = [
            {"$match": order_filter},
            {"$project": {"status": {"$ifNull": ["$status", "Received"]}, "total": _number("total"), "eta": _date("eta"), "date": _date("date")}},
            {"$group": {"_id": None, "total_po": {"$sum": 1}, "po_value": {"$sum": "$total"}, "completed_orders": {"$sum": {"$cond": [{"$eq": ["$status", "Completed"]}, 1, 0]}}, "open_orders": {"$sum": {"$cond": [{"$in": ["$status", INACTIVE_ORDER_STATUSES]}, 0, 1]}}, "overdue_orders": {"$sum": {"$cond": [{"$and": [{"$not": [{"$in": ["$status", INACTIVE_ORDER_STATUSES]}]}, {"$ne": ["$eta", None]}, {"$lt": ["$eta", current]}]}, 1, 0]}}}},
        ]

        target_summary = [
            {"$match": {**target_filter, "year": current.year}},
            {"$group": {"_id": None, "sales_target": {"$sum": _number("target")}}},
        ]

        recent_activities = [
            {"$match": activity_filter},
            {"$set": {"safe_date": _date("date"), "safe_status": {"$ifNull": ["$status", "Open"]}}},
            {"$sort": {"safe_date": -1, "created_at": -1}},
            {"$limit": 8},
            {"$project": {"_id": 0, "id": 1, "subject": 1, "activity_type": 1, "customer_name": 1, "sales_name": 1, "date": {"$cond": [{"$ne": ["$safe_date", None]}, {"$dateToString": {"date": "$safe_date", "format": "%Y-%m-%d"}}, None]}, "status": "$safe_status"}},
        ]

        risks = [
            {"$match": opportunity_filter},
            {"$set": {"safe_value": _number("value"), "safe_created": _date("created_at"), "safe_close": _date("target_close"), "safe_stage": {"$ifNull": ["$stage", "Unknown"]}},
            {"$match": {"safe_stage": {"$nin": ["Won", "Lost"]}}},
            {"$set": {"risk_reason": {"$switch": {"branches": [
                {"case": {"$and": [{"$ne": ["$safe_close", None]}, {"$lt": ["$safe_close", current]}]}, "then": "Expected close terlewat"},
                {"case": {"$and": [{"$ne": ["$safe_created", None]}, {"$lt": ["$safe_created", stalled_before]}]}, "then": "Tidak bergerak >30 hari"},
                {"case": {"in": [{"$ifNull": ["$next_action", ""]}, ["", None]]}, "then": "Next action belum diisi"},
            ], "default": None}}}},
            {"$match": {"risk_reason": {"$ne": None}}},
            {"$sort": {"safe_value": -1}},
            {"$limit": 8},
            {"$project": {"_id": 0, "id": 1, "opportunity_id": 1, "name": 1, "customer_name": {"$ifNull": ["$customer_name", "—"]}, "sales_name": 1, "value": "$safe_value", "stage": "$safe_stage", "expected_close": {"$cond": [{"$ne": ["$safe_close", None]}, {"$dateToString": {"date": "$safe_close", "format": "%Y-%m-%d"}}, None]}, "reason": "$risk_reason"}},
        ]

        year_start = datetime(current.year, 1, 1, tzinfo=timezone.utc)
        next_year = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
        monthly_orders = [
            {"$match": {**order_filter, "date": {"$gte": year_start, "$lt": next_year}}},
            {"$project": {"date": _date("date"), "total": _number("total")}},
            {"$group": {"_id": {"$month": "$date"}, "actual": {"$sum": "$total"}}},
        ]
        monthly_targets = [
            {"$match": {**target_filter, "year": current.year}},
            {"$group": {"_id": "$month", "target": {"$sum": _number("target")}}},
        ]

        (
            opportunity_rows,
            activity_totals,
            quotation_totals,
            order_totals,
            target_totals,
            customer_count,
            contact_count,
            lead_count,
            recent_rows,
            risk_rows,
            monthly_order_rows,
            monthly_target_rows,
        ) = await asyncio.gather(
            _many("opportunities", opportunity_summary),
            _one("activities", activity_summary),
            _one("quotations", quotation_summary),
            _one("purchase_orders", order_summary),
            _one("sales_targets", target_summary),
            db.customers.count_documents(customer_filter),
            db.contacts.count_documents(contact_filter),
            db.leads.count_documents(lead_filter),
            _many("activities", recent_activities),
            _many("opportunities", risks),
            _many("purchase_orders", monthly_orders),
            _many("sales_targets", monthly_targets),
        )

        by_stage: dict[str, dict[str, float]] = {}
        by_sales: dict[str, dict[str, float]] = {}
        for row in opportunity_rows:
            group = row.get("_id") or {}
            stage_name = group.get("stage") or "Unknown"
            sales_name = group.get("sales_name") or "Unassigned"
            count = int(row.get("count", 0))
            value = float(row.get("value", 0) or 0)
            weighted = float(row.get("weighted", 0) or 0)
            by_stage.setdefault(stage_name, {"count": 0, "value": 0.0, "weighted": 0.0})
            by_stage[stage_name]["count"] += count
            by_stage[stage_name]["value"] += value
            by_stage[stage_name]["weighted"] += weighted
            if stage_name not in ("Won", "Lost"):
                by_sales.setdefault(sales_name, {"count": 0, "value": 0.0})
                by_sales[sales_name]["count"] += count
                by_sales[sales_name]["value"] += value

        total_opportunities = sum(int(item["count"]) for item in by_stage.values())
        open_pipeline = sum(item["value"] for name, item in by_stage.items() if name not in ("Won", "Lost"))
        weighted_pipeline = sum(item["weighted"] for name, item in by_stage.items() if name not in ("Won", "Lost"))
        won_value = by_stage.get("Won", {}).get("value", 0.0)
        lost_value = by_stage.get("Lost", {}).get("value", 0.0)
        won_count = by_stage.get("Won", {}).get("count", 0)
        lost_count = by_stage.get("Lost", {}).get("count", 0)
        closed = won_count + lost_count

        pipeline_by_stage = [
            {"name": name, "count": int(by_stage.get(name, {}).get("count", 0)), "value": float(by_stage.get(name, {}).get("value", 0))}
            for name in [*REFERENCE_STAGES, *[name for name in by_stage if name not in REFERENCE_STAGES]]
        ]
        pipeline_by_salesperson = [
            {"name": name, "count": int(item["count"]), "value": float(item["value"])}
            for name, item in sorted(by_sales.items(), key=lambda pair: pair[1]["value"], reverse=True)[:10]
        ]

        actual_by_month = {int(row.get("_id")): float(row.get("actual", 0) or 0) for row in monthly_order_rows if row.get("_id")}
        target_by_month = {int(row.get("_id")): float(row.get("target", 0) or 0) for row in monthly_target_rows if row.get("_id")}
        monthly_sales = [
            {"month": f"{current.year}-{month:02d}", "label": MONTH_LABELS[month - 1], "actual": actual_by_month.get(month, 0), "target": target_by_month.get(month, 0)}
            for month in range(1, 13)
        ]

        activity_totals = activity_totals or {}
        quotation_totals = quotation_totals or {}
        order_totals = order_totals or {}
        target_totals = target_totals or {}
        sales_target = float(target_totals.get("sales_target", 0) or 0)
        quotation_value = float(quotation_totals.get("quotation_value", 0) or 0)
        po_value = float(order_totals.get("po_value", 0) or 0)

        return {
            "total_customer": int(customer_count),
            "total_contacts": int(contact_count),
            "total_leads": int(lead_count),
            "total_opportunities": total_opportunities,
            "open_pipeline": open_pipeline,
            "weighted_pipeline": weighted_pipeline,
            "won_value": won_value,
            "lost_value": lost_value,
            "win_rate": (won_count / closed * 100) if closed else 0,
            "total_quotation": int(quotation_totals.get("total_quotation", 0) or 0),
            "active_quotations": int(quotation_totals.get("active_quotations", 0) or 0),
            "quotation_value": quotation_value,
            "total_po": int(order_totals.get("total_po", 0) or 0),
            "po_value": po_value,
            "open_orders": int(order_totals.get("open_orders", 0) or 0),
            "completed_orders": int(order_totals.get("completed_orders", 0) or 0),
            "overdue_orders": int(order_totals.get("overdue_orders", 0) or 0),
            "activities": int(activity_totals.get("activities", 0) or 0),
            "overdue_activities": int(activity_totals.get("overdue_activities", 0) or 0),
            "sales_target": sales_target,
            "target_achievement": (po_value / sales_target * 100) if sales_target else 0,
            "pipeline_by_stage": pipeline_by_stage,
            "pipeline_by_salesperson": pipeline_by_salesperson,
            "monthly_sales_performance": monthly_sales,
            "recent_activities": recent_rows,
            "deal_risks": risk_rows,
            "generated_at": current,
        }
