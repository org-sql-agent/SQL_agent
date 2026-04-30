from typing import Literal

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant", "function"]
    content: str
    type: str | None = None
    summary: str | None = None
    data: dict | None = None


class InputModel(BaseModel):
    text: str
    history: list[HistoryMessage] = Field(default_factory=list)


class OutputModel(BaseModel):
    data: dict
    # compact 後的 LLM context，前端存著下次直接送，避免重複壓縮
    llm_history: list[dict] = Field(default_factory=list)
