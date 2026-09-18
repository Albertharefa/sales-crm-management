"""Compatibility patch for custom Customer Industry/Source values.

The Customer form uses the special option `Lainnya` and a manually entered
value.  Normalize that value before FastAPI/Pydantic validates the request so
MongoDB receives the actual text rather than the placeholder `Lainnya`.
"""

from typing import Any

from routers import customers


_CUSTOM_KEYS = {
    "industry": (
        "industry_other",
        "industry_custom",
        "custom_industry",
        "other_industry",
        "industryOther",
        "industryCustom",
        "customIndustry",
        "industry_lainnya",
    ),
    "source": (
        "source_other",
        "source_custom",
        "custom_source",
        "other_source",
        "sourceOther",
        "sourceCustom",
        "customSource",
        "source_lainnya",
    ),
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _custom_value(data: dict[str, Any], field: str) -> str:
    for key in _CUSTOM_KEYS[field]:
        value = _text(data.get(key))
        if value:
            return value
    return ""


def _normalize_payload(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)
    for field in ("industry", "source"):
        if _text(normalized.get(field)).lower() == "lainnya":
            custom = _custom_value(normalized, field)
            if custom:
                normalized[field] = custom
    return normalized


def _patch_model(model: type) -> None:
    # FastAPI/Pydantic v2 normally validates through model_validate(), so
    # patching only __init__ is not sufficient for request bodies.
    original_init = model.__init__
    original_model_validate = model.model_validate

    def patched_init(self, **data: Any):
        original_init(self, **_normalize_payload(data))

    @classmethod
    def patched_model_validate(cls, obj: Any, *args: Any, **kwargs: Any):
        return original_model_validate(_normalize_payload(obj), *args, **kwargs)

    model.__init__ = patched_init
    model.model_validate = patched_model_validate


_patch_model(customers.CustomerCreate)
_patch_model(customers.CustomerUpdate)
