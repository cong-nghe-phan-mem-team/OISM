from pydantic import BaseModel, Field
from typing import Any, Dict

class WebhookEventRequest(BaseModel):
    platform: str = Field(description="Tên nền tảng gửi webhook (vd: Shopee, GHN)")
    event_type: str = Field(description="Loại sự kiện (vd: ORDER_UPDATED)")
    payload: Dict[str, Any] = Field(description="Dữ liệu chi tiết của webhook")