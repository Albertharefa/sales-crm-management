from fastapi import APIRouter, Depends, HTTPException

from routers.deps import require_roles
from routers.common import audit
from services.demo_data_fixed import clear_demo_data, generate_demo_data

router = APIRouter(prefix="/admin/demo-data", tags=["admin-demo-data"])


@router.post("/generate")
async def generate_dummy_data(user: dict = Depends(require_roles("SUPER_ADMIN"))):
    try:
        result = await generate_demo_data()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Generate Dummy gagal dan seluruh data baru sudah di-rollback.") from exc

    try:
        await audit(user, "Generate Dummy", "Demo Data", None, result["counts"])
    except Exception:
        pass

    return {"success": True, "message": "Demo data generated successfully", **result}


@router.delete("/clear")
async def clear_dummy_data(user: dict = Depends(require_roles("SUPER_ADMIN"))):
    try:
        result = await clear_demo_data()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Clear Dummy gagal. Tidak ada data yang dihapus.") from exc

    try:
        await audit(user, "Clear Dummy", "Demo Data", None, result["deleted"])
    except Exception:
        pass

    return {"success": True, "message": "Demo data cleared successfully", **result}
