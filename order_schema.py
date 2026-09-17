from typing import List, Union
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sku_id: Union[int, str]
    quantity: int = Field(gt=0)
    # Backward-compatible field; backend uses ProductVariant.retailPrice as the source of truth.
    unit_price: Decimal | None = Field(default=None, ge=0)


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    branch_id: Union[int, str]
    sales_channel: str = Field(min_length=1, max_length=50)
    items: List[OrderItemSchema] = Field(min_length=1)
