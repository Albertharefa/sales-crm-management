from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Opportunity, OpportunityCreate, Paginated
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]


async def visible_sales_ids(user: dict) -> list[str] | None:
    """Return sales IDs visible to the current user; None means unrestricted."""
    role = str(user.get("role") or "").upper()
    if role == "SUPER_ADMIN":
        return None
    if role == "SALES_MANAGER":
        reports = await db.users.find(
            {"manager_id": user["id"], "role": "SALES"},
            {"_id": 0, "id": 1},
        ).to_list(1000)
        return [str(item["id"]) for item in reports if item.get("id")]
    return [str(user["id"])]


async def validate_sales_assignment(sales_id: str, user: dict) -> dict:
    """Validate a responsible salesperson and enforce the user hierarchy."""
    sales = await db.users.find_one(
        {"id": sales_id, "role": "SALES"},
        {"_id": 0, "id": 1, "name": 1, "role": 1, "status": 1, "manager_id": 1},
    )
    if not sales:
        raise HTTPException(status_code=400, detail="Sales penanggung jawab tidak valid")

    status = str(sales.get("status") or "Active").upper()
    if status in {"INACTIVE", "DISABLED"}:
        raise HTTPException(status_code=400, detail="Sales penanggung jawab tidak aktif")

    role = str(user.get("role") or "").upper()
    if role == "SALES" and sales["id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Sales hanya dapat membuat opportunity untuk dirinya sendiri")
    if role == "SALES_MANAGER" and sales.get("manager_id") != user.get("id"):
        raise HTTPException(status_code=403, detail="Sales tersebut bukan anggota team Anda")

    return sales


async def ensure_opportunity_access(doc: dict, user: dict) -> None:
    """Prevent users from viewing or changing opportunities outside their scope."""
    role = str(user.get("role") or "").upper()
    if role == "SUPER_ADMIN":
        return

    sales_id = str(doc.get("sales_id") or "")
    if role == "SALES" and sales_id == str(user.get("id")):
        return
    if role == "SALES_MANAGER":
        visible_ids = await visible_sales_ids(user) or []
        if sales_id in visible_ids:
            return

    raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke opportunity ini")


@router.get("", response_model=Paginated)
async def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    stage: str | None = None,
    sales_id: str | None = None,
    customer_id: str | None = None,
    user: dict = Depends(current_user),
):
    if stage and stage not in STAGES:
        raise HTTPException(status_code=422, detail="Stage tidak valid")

    visible_ids = await visible_sales_ids(user)
    filters: dict = {}
    if visible_ids is not None:
        filters["sales_id"] = {"$in": visible_ids}
    if sales_id:
        if visible_ids is not None and sales_id not in visible_ids:
            raise HTTPException(status_code=403, detail="Sales tersebut berada di luar scope Anda")
        filters["sales_id"] = sales_id
    if stage:
        filters["stage"] = stage
    if customer_id:
        filters["customer_id"] = customer_id

    return await page_collection("opportunities", page, page_size, search, filters)


@router.get("/sales-options")
async def sales_options(user: dict = Depends(current_user)):
    """Return only active Sales that the current user may assign."""
    visible_ids = await visible_sales_ids(user)
    query: dict = {
        "role": "SALES",
        "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]},
    }
    if visible_ids is not None:
        query["id"] = {"$in": visible_ids}

    users = await db.users.find(
        query,
        {"_id": 0, "id": 1, "user_id": 1, "name": 1},
    ).sort("name", 1).to_list(1000)
    return [
        {"id": str(item["id"]), "user_id": str(item.get("user_id") or ""), "name": str(item["name"])}
        for item in users
        if item.get("id") and item.get("name")
    ]


@router.get("/customer-options")
async def customer_options(user: dict = Depends(current_user)):
    """Return customers for the Sales Pipeline customer filter."""
    customers = await db.customers.find(
        {},
        {"_id": 0, "id": 1, "customer_id": 1, "name": 1, "company_name": 1},
    ).sort("name", 1).to_list(1000)

    result = []
    seen_ids = set()
    for customer in customers:
        customer_id = customer.get("id") or customer.get("customer_id")
        if not customer_id or customer_id in seen_ids:
            continue
        display_name = (
            customer.get("name")
            or customer.get("company_name")
            or customer.get("customer_id")
            or str(customer_id)
        )
        result.append({"id": str(customer_id), "name": str(display_name)})
        seen_ids.add(customer_id)
    return result


@router.get("/kanban")
async def kanban(
    sales_id: str | None = None,
    customer_id: str | None = None,
    user: dict = Depends(current_user),
):
    visible_ids = await visible_sales_ids(user)
    if sales_id and visible_ids is not None and sales_id not in visible_ids:
        raise HTTPException(status_code=403, detail="Sales tersebut berada di luar scope Anda")

    base_filters: dict = {}
    if visible_ids is not None:
        base_filters["sales_id"] = {"$in": visible_ids}
    if sales_id:
        base_filters["sales_id"] = sales_id
    if customer_id:
        base_filters["customer_id"] = customer_id

    result = []
    for stage in STAGES:
        query = {"stage": stage, **base_filters}
        items = await db.opportunities.find(query).sort("created_at", -1).to_list(100)
        for item in items:
            item.pop("_id", None)
        result.append({
            "stage": stage,
            "count": len(items),
            "value": sum(float(i.get("value", 0) or 0) for i in items),
            "items": items,
        })
    return result


@router.post("", response_model=Opportunity)
async def create_opportunity(
    payload: OpportunityCreate,
    user: dict = Depends(current_user),
):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")

    sales_id = payload.sales_id or user["id"]
    sales = await validate_sales_assignment(sales_id, user)

    count = await db.opportunities.count_documents({}) + 1
    payload_data = payload.model_dump(mode="json")
    payload_data["sales_id"] = sales["id"]

    doc = {
        "id": new_id(),
        "opportunity_id": f"OPP-{now().year}-{count:05d}",
        "customer_name": customer["name"],
        "sales_id": sales["id"],
        "sales_name": sales["name"],
        **payload_data,
        "created_at": now(),
    }

    await db.opportunities.insert_one(doc)
    await audit(
        user,
        "Create",
        "Sales Pipeline",
        doc["id"],
        {"name": doc["name"], "sales_name": doc["sales_name"]},
    )
    return Opportunity(**doc)


@router.patch("/{opportunity_id}/stage", response_model=Opportunity)
async def update_stage(
    opportunity_id: str,
    stage: str,
    loss_reason: str | None = None,
    user: dict = Depends(current_user),
):
    if stage not in STAGES:
        raise HTTPException(status_code=422, detail="Stage tidak valid")
    if stage == "Lost" and not loss_reason:
        raise HTTPException(status_code=422, detail="Loss reason wajib diisi")

    doc = await db.opportunities.find_one({"id": opportunity_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity tidak ditemukan")
    await ensure_opportunity_access(doc, user)

    update = {"stage": stage, "loss_reason": loss_reason}
    await db.opportunities.update_one({"id": opportunity_id}, {"$set": update})
    await audit(user, "Status Change", "Sales Pipeline", opportunity_id, update)
    return Opportunity(**{**doc, **update})
