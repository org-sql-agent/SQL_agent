from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.core.service.agent import ai_agent
from app.schemas.service.schema import InputModel, OutputModel
from app.utils.logger import setup_logger

logger = setup_logger("ServiceRouter")


router = APIRouter()


@router.post("/Service", response_model=OutputModel)
async def service(input: InputModel) -> OutputModel:
    history = [msg.model_dump() for msg in input.history]
    query = input.text

    # Run sync heavy work in threadpool to avoid blocking event loop workers.
    result = await run_in_threadpool(ai_agent, history, query)

    return OutputModel(data=result)
