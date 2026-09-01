import json
import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from lib.db import db
from models.ai import (
    AIChatRequest,
    AIContextOption,
    AIConversationDetail,
    AIMessage,
    AISaveRequest,
    AISavedNote,
)
from routers.common import audit, new_id, now
from routers.deps import current_user


router = APIRouter(prefix="/ai", tags=["ai"])

MODEL_NAME = "gpt-5.4"
OPENAI_API_URL = "https://api.openai.com/v1/responses"

logger = logging.getLogger(__name__)


def sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def visible_filter(
    user: dict,
    owner_id_field: str = "sales_id",
    owner_name_field: str = "sales_name",
) -> dict:
    if user.get("role") == "SUPER_ADMIN":
        return {}

    if user.get("role") == "SALES_MANAGER":
        reports = await db.users.find(
            {"manager_id": user["id"]},
            {"id": 1, "name": 1},
        ).to_list(100)

        ids = [user["id"], *[item["id"] for item in reports]]
        names = [user["name"], *[item["name"] for item in reports]]

        return {
            "$or": [
                {owner_id_field: {"$in": ids}},
                {owner_name_field: {"$in": names}},
            ]
        }

    return {
        "$or": [
            {owner_id_field: user["id"]},
            {owner_name_field: user["name"]},
        ]
    }


async def find_visible(
    collection: str,
    record_id: str,
    user: dict,
    id_field: str = "id",
) -> dict:
    query: dict[str, Any] = {id_field: record_id}
    query.update(await visible_filter(user))

    record = await db[collection].find_one(
        query,
        {"_id": 0},
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Konteks CRM tidak ditemukan atau tidak dapat diakses",
        )

    return record


async def build_context(
    context_type: str,
    context_id: str | None,
    user: dict,
) -> str:

    if context_type == "dashboard":
        visibility = await visible_filter(user)

        opportunities = await db.opportunities.find(
            visibility,
            {
                "_id": 0,
                "name": 1,
                "customer_name": 1,
                "value": 1,
                "probability": 1,
                "stage": 1,
                "target_close": 1,
                "next_action": 1,
            },
        ).to_list(500)

        open_items = [
            item
            for item in opportunities
            if item.get("stage") not in ["Won", "Lost"]
        ]

        by_stage: dict[str, dict[str, float | int]] = {}

        for item in opportunities:
            stage = item.get("stage", "Unknown")

            bucket = by_stage.setdefault(
                stage,
                {
                    "count": 0,
                    "value": 0,
                },
            )

            bucket["count"] = int(bucket["count"]) + 1
            bucket["value"] = float(bucket["value"]) + float(
                item.get("value", 0)
            )

        context = {
            "open_pipeline": sum(
                float(item.get("value", 0))
                for item in open_items
            ),
            "weighted_pipeline": sum(
                float(item.get("value", 0))
                * float(item.get("probability", 0))
                / 100
                for item in open_items
            ),
            "pipeline_by_stage": by_stage,
            "upcoming_deals": sorted(
                open_items,
                key=lambda item: item.get("target_close")
                or "9999-12-31",
            )[:12],
        }

        return json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )

    if not context_id:
        raise HTTPException(
            status_code=422,
            detail="Pilih record CRM untuk digunakan sebagai konteks AI",
        )

    if context_type == "customer":
        record = await find_visible(
            "customers",
            context_id,
            user,
        )

        related_filter = await visible_filter(user)
        related_filter["customer_id"] = context_id

        opportunities = await db.opportunities.find(
            related_filter,
            {
                "_id": 0,
                "name": 1,
                "stage": 1,
                "value": 1,
                "probability": 1,
                "target_close": 1,
                "next_action": 1,
            },
        ).sort(
            "created_at",
            -1,
        ).to_list(25)

        activities = await db.activities.find(
            related_filter,
            {
                "_id": 0,
                "subject": 1,
                "activity_type": 1,
                "date": 1,
                "status": 1,
                "next_follow_up": 1,
            },
        ).sort(
            "created_at",
            -1,
        ).to_list(20)

        quotations = await db.quotations.find(
            {"customer_id": context_id},
            {
                "_id": 0,
                "number": 1,
                "status": 1,
                "grand_total": 1,
                "date": 1,
            },
        ).sort(
            "created_at",
            -1,
        ).to_list(20)

        return json.dumps(
            {
                "customer": record,
                "opportunities": opportunities,
                "recent_activities": activities,
                "quotations": quotations,
            },
            ensure_ascii=False,
            default=str,
        )

    if context_type == "opportunity":
        record = await find_visible(
            "opportunities",
            context_id,
            user,
        )

        activities = await db.activities.find(
            {"opportunity_id": context_id},
            {"_id": 0},
        ).sort(
            "created_at",
            -1,
        ).to_list(20)

        return json.dumps(
            {
                "opportunity": record,
                "activities": activities,
            },
            ensure_ascii=False,
            default=str,
        )

    if context_type == "quotation":
        record = await find_visible(
            "quotations",
            context_id,
            user,
        )

        return json.dumps(
            {
                "quotation": record,
            },
            ensure_ascii=False,
            default=str,
        )

    raise HTTPException(
        status_code=422,
        detail="Tipe konteks AI tidak valid",
    )


def system_prompt(capability: str) -> str:

    roles = {
        "sales_copilot": (
            "Anda adalah Sales Copilot senior untuk CRM industri "
            "B2B Indonesia. Ringkas fakta, identifikasi risiko, "
            "sarankan next action konkret, dan bantu menulis "
            "follow-up yang profesional."
        ),
        "report_analyst": (
            "Anda adalah analis sales enterprise. Jawab pertanyaan "
            "hanya dari angka konteks yang diberikan, tunjukkan "
            "rumus singkat, tren, risiko, dan tindakan yang disarankan."
        ),
        "quotation_writer": (
            "Anda adalah spesialis quotation industrial. Buat "
            "deskripsi item, scope, asumsi, exclusions, delivery "
            "terms, dan commercial notes yang jelas tanpa mengubah "
            "harga atau angka sumber."
        ),
    }

    role_prompt = roles.get(
        capability,
        roles["sales_copilot"],
    )

    return (
        role_prompt
        + " Gunakan Bahasa Indonesia kecuali diminta lain."
        + " Jangan mengarang data."
        + " Bedakan fakta, asumsi, dan rekomendasi."
        + " Jangan pernah mengklaim telah mengubah CRM;"
        + " penyimpanan hanya terjadi setelah konfirmasi pengguna"
        + " di aplikasi."
        + " Jangan ungkap password, token, secret,"
        + " atau data di luar konteks yang diberikan."
    )


@router.get(
    "/context-options",
    response_model=list[AIContextOption],
)
async def context_options(
    context_type: str = Query(...),
    user: dict = Depends(current_user),
):

    visibility = await visible_filter(user)

    if context_type == "customer":
        docs = await db.customers.find(
            visibility,
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "industry": 1,
                "city": 1,
            },
        ).sort(
            "name",
            1,
        ).limit(100).to_list(100)

        return [
            AIContextOption(
                id=item["id"],
                name=item["name"],
                description=(
                    f"{item.get('industry', '—')} · "
                    f"{item.get('city', '—')}"
                ),
            )
            for item in docs
        ]

    if context_type == "opportunity":
        docs = await db.opportunities.find(
            visibility,
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "customer_name": 1,
                "stage": 1,
            },
        ).sort(
            "created_at",
            -1,
        ).limit(100).to_list(100)

        return [
            AIContextOption(
                id=item["id"],
                name=item["name"],
                description=(
                    f"{item.get('customer_name', '—')} · "
                    f"{item.get('stage', '—')}"
                ),
            )
            for item in docs
        ]

    if context_type == "quotation":
        docs = await db.quotations.find(
            visibility,
            {
                "_id": 0,
                "id": 1,
                "number": 1,
                "customer_name": 1,
                "status": 1,
            },
        ).sort(
            "created_at",
            -1,
        ).limit(100).to_list(100)

        return [
            AIContextOption(
                id=item["id"],
                name=item["number"],
                description=(
                    f"{item.get('customer_name', '—')} · "
                    f"{item.get('status', '—')}"
                ),
            )
            for item in docs
        ]

    return []


@router.get(
    "/conversations/{conversation_id}",
    response_model=AIConversationDetail,
)
async def conversation_history(
    conversation_id: str,
    user: dict = Depends(current_user),
):

    conversation = await db.ai_conversations.find_one(
        {
            "id": conversation_id,
            "user_id": user["id"],
        },
        {"_id": 0},
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Percakapan AI tidak ditemukan",
        )

    messages = await db.ai_messages.find(
        {
            "conversation_id": conversation_id,
        },
        {"_id": 0},
    ).sort(
        "created_at",
        1,
    ).limit(100).to_list(100)

    return AIConversationDetail(
        **conversation,
        messages=[
            AIMessage(**message)
            for message in messages
        ],
    )


async def call_openai(
    api_key: str,
    instructions: str,
    user_input: str,
) -> str:

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "instructions": instructions,
        "input": user_input,
        "reasoning": {
            "effort": "low",
        },
        "max_output_tokens": 900,
    }

    timeout = httpx.Timeout(
        90.0,
        connect=15.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
    ) as client:

        response = await client.post(
            OPENAI_API_URL,
            headers=headers,
            json=payload,
        )

        if response.status_code >= 400:
            logger.error(
                "OpenAI API error %s: %s",
                response.status_code,
                response.text[:2000],
            )

            raise RuntimeError(
                f"OpenAI API returned {response.status_code}"
            )

        data = response.json()

    output_text = data.get("output_text")

    if output_text:
        return output_text.strip()

    # Fallback parser in case output_text is not present.
    collected: list[str] = []

    for item in data.get("output", []):
        for content in item.get("content", []):
            text_value = content.get("text")

            if isinstance(text_value, str):
                collected.append(text_value)

    answer = "".join(collected).strip()

    if not answer:
        raise RuntimeError(
            "OpenAI returned an empty response"
        )

    return answer


@router.post("/chat/stream")
async def chat_stream(
    payload: AIChatRequest,
    user: dict = Depends(current_user),
):

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY belum dikonfigurasi",
        )

    crm_context = await build_context(
        payload.context_type,
        payload.context_id,
        user,
    )

    conversation = None

    if payload.conversation_id:
        conversation = await db.ai_conversations.find_one(
            {
                "id": payload.conversation_id,
                "user_id": user["id"],
            }
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Percakapan AI tidak ditemukan",
            )

    if not conversation:
        created = now()

        conversation = {
            "id": new_id(),
            "user_id": user["id"],
            "title": payload.prompt[:70],
            "context_type": payload.context_type,
            "context_id": payload.context_id,
            "created_at": created,
            "updated_at": created,
        }

        await db.ai_conversations.insert_one(
            conversation
        )

    conversation_id = conversation["id"]

    user_message = {
        "id": new_id(),
        "conversation_id": conversation_id,
        "role": "user",
        "content": payload.prompt,
        "capability": payload.capability,
        "context_type": payload.context_type,
        "context_id": payload.context_id,
        "created_at": now(),
    }

    await db.ai_messages.insert_one(
        user_message
    )

    previous = await db.ai_messages.find(
        {
            "conversation_id": conversation_id,
            "id": {
                "$ne": user_message["id"],
            },
        },
        {
            "_id": 0,
            "role": 1,
            "content": 1,
        },
    ).sort(
        "created_at",
        -1,
    ).limit(8).to_list(8)

    history = "\n".join(
        f"{item['role'].upper()}: {item['content']}"
        for item in reversed(previous)
    )

    assistant_message_id = new_id()

    async def event_generator():

        yield sse(
            {
                "type": "meta",
                "conversation_id": conversation_id,
                "assistant_message_id": assistant_message_id,
                "model": MODEL_NAME,
            }
        )

        try:

            llm_input = (
                f"RIWAYAT PERCAKAPAN:\n"
                f"{history or '(baru)'}\n\n"
                f"KONTEKS CRM TERPILIH "
                f"({payload.context_type}):\n"
                f"{crm_context}\n\n"
                f"PERMINTAAN PENGGUNA:\n"
                f"{payload.prompt}"
            )

            answer = await call_openai(
                api_key=api_key,
                instructions=system_prompt(
                    payload.capability
                ),
                user_input=llm_input,
            )

            yield sse(
                {
                    "type": "delta",
                    "content": answer,
                }
            )

            assistant_message = {
                "id": assistant_message_id,
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": answer,
                "capability": payload.capability,
                "context_type": payload.context_type,
                "context_id": payload.context_id,
                "created_at": now(),
            }

            await db.ai_messages.insert_one(
                assistant_message
            )

            await db.ai_conversations.update_one(
                {
                    "id": conversation_id,
                },
                {
                    "$set": {
                        "updated_at": now(),
                        "context_type": payload.context_type,
                        "context_id": payload.context_id,
                    }
                },
            )

            await audit(
                user,
                "Generate",
                "AI Copilot",
                assistant_message_id,
                {
                    "capability": payload.capability,
                    "context_type": payload.context_type,
                    "context_id": payload.context_id,
                    "model": MODEL_NAME,
                },
            )

            yield sse(
                {
                    "type": "done",
                    "conversation_id": conversation_id,
                    "assistant_message_id": assistant_message_id,
                }
            )

        except Exception as exc:

            logger.exception(
                "AI chat failed: %s",
                exc,
            )

            yield sse(
                {
                    "type": "error",
                    "message": (
                        "AI sedang tidak dapat merespons. "
                        "Silakan coba lagi beberapa saat."
                    ),
                }
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/notes/confirm",
    response_model=AISavedNote,
)
async def confirm_ai_note(
    payload: AISaveRequest,
    user: dict = Depends(current_user),
):

    conversation = await db.ai_conversations.find_one(
        {
            "id": payload.conversation_id,
            "user_id": user["id"],
        }
    )

    message = await db.ai_messages.find_one(
        {
            "id": payload.message_id,
            "conversation_id": payload.conversation_id,
            "role": "assistant",
        }
    )

    if not conversation or not message:
        raise HTTPException(
            status_code=404,
            detail="Draft AI tidak ditemukan",
        )

    if payload.target_type != "dashboard":

        if not payload.target_id:
            raise HTTPException(
                status_code=422,
                detail="Target catatan wajib dipilih",
            )

        collection = {
            "customer": "customers",
            "opportunity": "opportunities",
            "quotation": "quotations",
        }[payload.target_type]

        await find_visible(
            collection,
            payload.target_id,
            user,
        )

    note = {
        "id": new_id(),
        "target_type": payload.target_type,
        "target_id": payload.target_id,
        "title": payload.title,
        "content": message["content"],
        "source": MODEL_NAME,
        "conversation_id": payload.conversation_id,
        "message_id": payload.message_id,
        "created_by": user["id"],
        "created_at": now(),
    }

    await db.notes.insert_one(note)

    await audit(
        user,
        "Confirm Save",
        "AI Copilot",
        note["id"],
        {
            "target_type": payload.target_type,
            "target_id": payload.target_id,
            "message_id": payload.message_id,
        },
    )

    return AISavedNote(**note)
