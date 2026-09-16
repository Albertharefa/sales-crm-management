import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from lib.db import db

STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]
INACTIVE_QUOTATIONS = ["Accepted", "Rejected", "Expired", "Cancelled"]
INACTIVE_ORDERS = ["Completed", "Cancelled"]
INACTIVE_ACTIVITIES = ["Completed", "Cancelled"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


async def visibility(user: dict) -> dict[str, Any]:
    role = str(user.get("role") or "").upper()
    if role == "SUPER_ADMIN":
        return {}
    if role == "SALES_MANAGER":
        reports = await db.users.find({"manager_id": user["id"]}, {"id": 1, "name": 1}).to_list(100)
        ids = [user["id"], *[row["id"] for row in reports]]
        names = [user["name"], *[row["name"] for row in reports]]
        return {"$or": [{"sales_id": {"$in": ids}}, {"sales_name": {"$in": names}}]}
    return {"$or": [{"sales_id": user["id"]}, {"sales_name": user["name"]}]}


def scope(base: dict, *extras: dict | None) -> dict:
    clauses = [base, *[item for item in extras if item]]
    clauses = [item for item in clauses if item]
    if not clauses:
        return {}
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def number(field: str) -> dict:
    return {"$convert": {"input": f"${field}", "to": "double", "onError": 0, "onNull": 0}}


class UltraFastDashboardService:
    async def get_metrics(self, user: dict, period: str | None = None, sales_id: str | None = None, stage: str | None = None, customer_id: str | None = None) -> dict[str, Any]:
        if stage and stage not in STAGES:
            raise HTTPException(status_code=422, detail="Stage dashboard tidak valid")

        now = datetime.now(timezone.utc)
        days = {"30d": 30, "90d": 90, "365d": 365}.get(str(period or "").lower())
        since = now.timestamp() - days * 86400 if days else None
        base = await visibility(user)
        sales_filter = {"sales_id": sales_id} if sales_id else None
        customer_filter = {"customer_id": customer_id} if customer_id else None
        date_filter = {"created_at": {"$gte": datetime.fromtimestamp(since, tz=timezone.utc)}} if since else None
        opp_filter = scope(base, sales_filter, customer_filter, date_filter, {"stage": stage} if stage else None)
        activity_filter = scope(base, sales_filter, customer_filter, {"date": {"$gte": datetime.fromtimestamp(since, tz=timezone.utc)}} if since else None)
        quotation_filter = scope(base, sales_filter, customer_filter, {"date": {"$gte": datetime.fromtimestamp(since, tz=timezone.utc)}} if since else None)
        order_filter = scope(base, sales_filter, customer_filter, {"date": {"$gte": datetime.fromtimestamp(since, tz=timezone.utc)}} if since else None)

        opp = [{"$match": opp_filter}, {"$project": {"stage": {"$ifNull": ["$stage", "Unknown"]}, "sales_name": {"$ifNull": ["$sales_name", "Unassigned"]}, "value": number("value"), "probability": number("probability")}}, {"$group": {"_id": {"stage": "$stage", "sales_name": "$sales_name"}, "count": {"$sum": 1}, "value": {"$sum": "$value"}, "weighted": {"$sum": {"$cond": [{"$in": ["$stage", ["Won", "Lost"]]}, 0, {"$multiply": ["$value", {"$divide": ["$probability", 100]}]}]}}}}]
        quotation = [{"$match": quotation_filter}, {"$project": {"status": {"$ifNull": ["$status", "Draft"]}, "value": number("grand_total")}}, {"$group": {"_id": None, "total": {"$sum": 1}, "active": {"$sum": {"$cond": [{"$in": ["$status", INACTIVE_QUOTATIONS]}, 0, 1]}}, "value": {"$sum": {"$cond": [{"$in": ["$status", INACTIVE_QUOTATIONS]}, 0, "$value"]}}}}]
        orders = [{"$match": order_filter}, {"$project": {"status": {"$ifNull": ["$status", "Received"]}, "value": number("total"), "eta": 1}}, {"$group": {"_id": None, "total": {"$sum": 1}, "value": {"$sum": "$value"}, "completed": {"$sum": {"$cond": [{"$eq": ["$status", "Completed"]}, 1, 0]}}, "open": {"$sum": {"$cond": [{"$in": ["$status", INACTIVE_ORDERS]}, 0, 1]}}, "overdue": {"$sum": {"$cond": [{"$and": [{"$not": [{"$in": ["$status", INACTIVE_ORDERS]}]}, {"$lt": ["$eta", now]}]}, 1, 0]}}}}]
        activities = [{"$match": activity_filter}, {"$project": {"status": {"$ifNull": ["$status", "Open"]}, "next": 1}}, {"$group": {"_id": None, "total": {"$sum": 1}, "overdue": {"$sum": {"$cond": [{"$and": [{"$not": [{"$in": ["$status", INACTIVE_ACTIVITIES]}]}, {"$lt": ["$next", now]}]}, 1, 0]}}}}]
        targets = [{"$match": {**base, "year": now.year}}, {"$group": {"_id": None, "target": {"$sum": number("target")}}}]

        opp_rows, quotation_row, order_row, activity_row, target_row, customers, contacts, leads, recent = await asyncio.gather(
            db.opportunities.aggregate(opp, allowDiskUse=True).to_list(500),
            db.quotations.aggregate(quotation, allowDiskUse=True).to_list(1),
            db.purchase_orders.aggregate(orders, allowDiskUse=True).to_list(1),
            db.activities.aggregate(activities, allowDiskUse=True).to_list(1),
            db.sales_targets.aggregate(targets, allowDiskUse=True).to_list(1),
            db.customers.count_documents(scope(base, sales_filter, customer_filter, date_filter)),
            db.contacts.count_documents(scope(base, sales_filter, customer_filter, date_filter)),
            db.leads.count_documents(scope(base, sales_filter, customer_filter, date_filter)),
            db.activities.find(activity_filter, {"_id": 0, "id": 1, "subject": 1, "activity_type": 1, "customer_name": 1, "sales_name": 1, "date": 1, "status": 1}).sort("date", -1).limit(8).to_list(8),
        )

        by_stage: dict[str, dict[str, float]] = {}
        by_sales: dict[str, dict[str, float]] = {}
        for row in opp_rows:
            key = row.get("_id") or {}
            name = key.get("stage") or "Unknown"
            seller = key.get("sales_name") or "Unassigned"
            item = by_stage.setdefault(name, {"count": 0, "value": 0.0, "weighted": 0.0})
            item["count"] += int(row.get("count", 0))
            item["value"] += float(row.get("value", 0) or 0)
            item["weighted"] += float(row.get("weighted", 0) or 0)
            if name not in ("Won", "Lost"):
                seller_item = by_sales.setdefault(seller, {"count": 0, "value": 0.0})
                seller_item["count"] += int(row.get("count", 0))
                seller_item["value"] += float(row.get("value", 0) or 0)

        open_pipeline = sum(v["value"] for k, v in by_stage.items() if k not in ("Won", "Lost"))
        weighted = sum(v["weighted"] for k, v in by_stage.items() if k not in ("Won", "Lost"))
        won = by_stage.get("Won", {}).get("value", 0.0)
        lost = by_stage.get("Lost", {}).get("value", 0.0)
        won_count = by_stage.get("Won", {}).get("count", 0)
        lost_count = by_stage.get("Lost", {}).get("count", 0)
        closed = won_count + lost_count
        q = quotation_row[0] if quotation_row else {}
        o = order_row[0] if order_row else {}
        a = activity_row[0] if activity_row else {}
        t = target_row[0] if target_row else {}
        po_value = float(o.get("value", 0) or 0)
        target = float(t.get("target", 0) or 0)

        return {
            "total_customer": int(customers), "total_contacts": int(contacts), "total_leads": int(leads),
            "total_opportunities": sum(v["count"] for v in by_stage.values()), "open_pipeline": open_pipeline,
            "weighted_pipeline": weighted, "won_value": won, "lost_value": lost, "win_rate": (won_count / closed * 100) if closed else 0,
            "total_quotation": int(q.get("total", 0) or 0), "active_quotations": int(q.get("active", 0) or 0), "quotation_value": float(q.get("value", 0) or 0),
            "total_po": int(o.get("total", 0) or 0), "po_value": po_value, "open_orders": int(o.get("open", 0) or 0),
            "completed_orders": int(o.get("completed", 0) or 0), "overdue_orders": int(o.get("overdue", 0) or 0),
            "activities": int(a.get("total", 0) or 0), "overdue_activities": int(a.get("overdue", 0) or 0),
            "sales_target": target, "target_achievement": (po_value / target * 100) if target else 0,
            "pipeline_by_stage": [{"name": name, "count": int(by_stage.get(name, {}).get("count", 0)), "value": float(by_stage.get(name, {}).get("value", 0))} for name in [*STAGES, *[x for x in by_stage if x not in STAGES]]],
            "pipeline_by_salesperson": [{"name": name, "count": int(v["count"]), "value": float(v["value"])} for name, v in sorted(by_sales.items(), key=lambda x: x[1]["value"], reverse=True)[:10]],
            "monthly_sales_performance": [], "recent_activities": recent, "deal_risks": [], "generated_at": now,
        }
