from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/proxy", tags=["proxy"])


@router.get("/")
async def proxy():
    return {"status": "ok", "message": "Proxy endpoint"}
