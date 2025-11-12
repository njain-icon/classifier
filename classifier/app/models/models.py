from typing import List, Optional, Union
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field


class AiDataModel(BaseModel):
    data: Optional[Union[list, str]] = None
    entityDetails: Optional[dict] = {}

class ReqClassifier(BaseModel):
    text: str
    anonymize: Optional[bool] = Field(default=False)
    country_list : List[str] = Field(default=["US"])

class ClassifierJsonResponse:
    """
    Response class for custom json response
    """

    @classmethod
    def build(
        cls,
        body: Optional[dict] = None,
        status_code: int = 200,
    ):
        return JSONResponse(status_code=status_code, content=jsonable_encoder(body))
