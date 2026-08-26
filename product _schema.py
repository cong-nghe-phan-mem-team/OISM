from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class VariantCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sku: str = Field(min_length=1, max_length=100)
    barcode: Optional[str] = Field(default=None, max_length=100)
    retailPrice: Decimal = Field(default=Decimal("0"), ge=0)
    wholesalePrice: Decimal = Field(default=Decimal("0"), ge=0)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=255)
    categoryId: Optional[int] = None
    brandId: Optional[int] = None
    variants: List[VariantCreateSchema] = Field(min_length=1)
