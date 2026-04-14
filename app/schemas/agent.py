from typing import Any, Literal

from pydantic import BaseModel


class AgentResponse(BaseModel):
    type: Literal["text", "image", "echarts"]
    content: str
    summary: str | None = None
    data: dict[str, Any] | None = None
