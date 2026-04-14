from pydantic import BaseModel
from typing import Literal

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant", "function"]
    content: str
    type: str | None = None
    summary: str | None = None
    data: dict | None = None

class InputModel(BaseModel):
    text: str
    history: list[HistoryMessage] = []


class OutputModel(BaseModel):
    data: dict