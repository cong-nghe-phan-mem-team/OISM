import pytest
from unittest.mock import MagicMock, patch
from app.services.pos_service import POSService
from app.schemas.pos import POSCheckoutRequest, POSItemSchema

@pytest.mark.asyncio
async def test_process_checkout_success():
    payload=POSCheckoutRequest(items=[POSItemSchema(sku="SKU-001",quantity=2,price=50000)],discount=10000,payment_method="Cash")
    mock_saved={"order":{"orderId":1},"items":[{"sku":"SKU-001","quantity":2,"price":50000}]}
    with patch("app.repositories.pos_repo.POSRepository.save_pos_receipt",return_value=mock_saved) as mock_save:
        result=POSService.process_checkout(MagicMock(),1,1,payload)
        assert result["message"]=="Thanh toán thành công!"
        assert result["receipt"]==mock_saved
        mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_process_checkout_empty_cart_raises_error():
    payload=POSCheckoutRequest(items=[],discount=0,payment_method="Cash")
    with pytest.raises(ValueError,match="Giỏ hàng trống!"):
        POSService.process_checkout(MagicMock(),1,1,payload)
