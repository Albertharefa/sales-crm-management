"""Legacy seed module kept for backwards-compatible startup imports.

Demo data is managed explicitly through SUPER_ADMIN endpoints. Application
startup must never delete CRM production data or generated test data.
"""


async def seed_demo_data():
    """Compatibility no-op: never seed or delete data during startup."""
    return None
