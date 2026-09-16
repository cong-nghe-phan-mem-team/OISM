from typing import Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class PurchaseReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skuId: Union[int, str]
    branchId: Union[int, str]
    importQuantity: int = Field(gt=0)
    importUnitPrice: Decimal = Field(ge=0)
    referenceId: Optional[str] = Field(default=None, max_length=255)
