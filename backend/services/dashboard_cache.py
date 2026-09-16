import asyncio
import copy
import time
from typing import Any

from services.dashboard_ultrafast import UltraFastDashboardService


class CachedDashboardService:
    """Short-lived in-process cache for the dashboard API.

    The dashboard is read-heavy and changes much less frequently than it is
    opened/refreshed. A short TTL removes repeated Mongo aggregations while
    keeping the dashboard effectively live for normal CRM usage.
    """

    TTL_SECONDS = 15.0

    def __init__(self) -> None:
        self._service = UltraFastDashboardService()
        self._cache: dict[tuple[str, str, str, str, str], tuple[float, dict[str, Any]]] = {}
        self._locks: dict[tuple[str, str, str, str, str], asyncio.Lock] = {}

    @staticmethod
    def _key(user: dict, period: str | None, sales_id: str | None, stage: str | None, customer_id: str | None) -> tuple[str, str, str, str, str]:
        return (
            str(user.get("id") or ""),
            str(period or ""),
            str(sales_id or ""),
            str(stage or ""),
            str(customer_id or ""),
        )

    async def get_metrics(self, user: dict, period: str | None = None, sales_id: str | None = None, stage: str | None = None, customer_id: str | None = None) -> dict[str, Any]:
        key = self._key(user, period, sales_id, stage, customer_id)
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.TTL_SECONDS:
            return copy.deepcopy(cached[1])

        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self._cache.get(key)
            if cached and time.monotonic() - cached[0] < self.TTL_SECONDS:
                return copy.deepcopy(cached[1])

            metrics = await self._service.get_metrics(
                user,
                period=period,
                sales_id=sales_id,
                stage=stage,
                customer_id=customer_id,
            )
            self._cache[key] = (time.monotonic(), copy.deepcopy(metrics))
            return metrics

    async def warm(self, user: dict) -> None:
        """Populate the default dashboard before the first browser request."""
        try:
            await self.get_metrics(user)
        except Exception:
            # Warm-up must never prevent the application from starting.
            return

    def clear(self) -> None:
        self._cache.clear()
