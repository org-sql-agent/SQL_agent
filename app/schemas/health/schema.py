from pydantic import BaseModel


class PingResponse(BaseModel):
    reply: str
