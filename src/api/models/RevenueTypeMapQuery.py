from typing import List, Any
from pydantic.main import BaseModel


class RevenueTypeMapQuery(BaseModel):
    product_id: str
    agency: str
    dealType: str
    lineOfBusiness: str
    politicalSpend: str
    customerOrderType: str