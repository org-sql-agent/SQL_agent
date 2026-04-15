from fastapi import APIRouter

from app.core.service.agent import ai_agent
from app.schemas.service.schema import InputModel, OutputModel
from app.utils.logger import setup_logger

logger = setup_logger("ServiceRouter")


router = APIRouter()


@router.post("/Service", response_model=OutputModel)
async def service(input: InputModel) -> OutputModel:

    history = [msg.model_dump() for msg in input.history]
    query = input.text

    result = ai_agent(history, query)

    return OutputModel(data=result)
