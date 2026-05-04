from fastapi import APIRouter

from app.api.schemas.health import PingResponse

router = APIRouter()


@router.get("/", summary="Health check", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse(reply="pong")
