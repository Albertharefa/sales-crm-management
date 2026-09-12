"""Legacy seed module kept for backwards-compatible startup imports.

Demo data is now managed explicitly through the SUPER_ADMIN endpoints:
POST /api/v1/admin/demo-data/generate
DELETE /api/v1/admin/demo-data/clear

Application startup must never delete CRM production data or generated test
data. This function is intentionally a no-op.
"""


async def seed_demo_data():
    """Compatibility no-op: never seed or delete data during startup."""
    return None
