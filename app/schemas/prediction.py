from typing import Literal

from pydantic import BaseModel


class PredictionRequest(BaseModel):
    target: Literal["Pclass", "Sex", "Age", "Fare", "Survived"]
    Pclass: int | None = None
    Sex: int | None = None
    Age: float | None = None
    Fare: float | None = None
    Survived: int | None = None
    model_name: str | None = None
