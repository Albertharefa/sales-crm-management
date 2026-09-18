"""Compatibility patch for custom Customer Industry/Source values.

The Customer form can use the special option `Lainnya` and send the manually
entered value under a custom field.  Older frontend builds used several
possible names for those fields.  Normalize them at the Pydantic model
boundary so the existing Customers router persists the actual text in
MongoDB without changing the customer API contract.
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


def _patch_model(model: type) -> None:
    original_init = model.__init__

    def patched_init(self, **data: Any):
        for field in ("industry", "source"):
            selected = _text(data.get(field))
            if selected.lower() == "lainnya":
                custom = _custom_value(data, field)
                if custom:
                    data[field] = custom
        original_init(self, **data)

    model.__init__ = patched_init


_patch_model(customers.CustomerCreate)
_patch_model(customers.CustomerUpdate)
