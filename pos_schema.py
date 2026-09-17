from typing import List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class POSItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)
    # Backward-compatible field; backend uses ProductVariant.retailPrice as the source of truth.
    price: Decimal | None = Field(default=None, ge=0)


class POSCheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[POSItemSchema]
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_method: str = Field(pattern="^(Cash|Card|QR)$")
