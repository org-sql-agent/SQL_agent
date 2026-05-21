import os

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI

from app.api.schemas.agent import InputModel, OutputModel
from app.config.settings import OPENAI_MODEL
from app.db.dao.titanic_dao import TitanicDAO
from app.services.agent_service import AgentService
from app.services.chart_service import ChartService
from app.utils.logger import setup_logger

logger = setup_logger("AgentRouter")
router = APIRouter()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_dao = TitanicDAO()
_chart_service = ChartService(_client, OPENAI_MODEL)
_agent_service = AgentService(_dao, _chart_service, _client, OPENAI_MODEL)


@router.post("/Service", response_model=OutputModel)
async def service(input: InputModel) -> OutputModel:
    history = [msg.model_dump() for msg in input.history]
    result, compacted_base = await run_in_threadpool(
        _agent_service.run, history, input.text
    )
    return OutputModel(data=result, llm_history=compacted_base)
