# app/api/routes/health.py
from fastapi import APIRouter

from app.schemas.health.schema import PingResponse

router = APIRouter()


@router.get(
    "/",
    summary="Health check",
    response_model=PingResponse,
)
async def ping() -> PingResponse:
    """
    Simple API to check if the server is alive.
    """
    return PingResponse(reply="pong")
