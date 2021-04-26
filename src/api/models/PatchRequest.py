from typing import List, Any
from pydantic.main import BaseModel


class PatchRequest(BaseModel):
    op: str
    path: str
    value: Any
