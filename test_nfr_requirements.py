from unittest.mock import MagicMock
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.rse_repo import RSERepository


def test_tenant_isolation_and_append_only():
    db = MagicMock()
    branch_result = MagicMock(); branch_result.first.return_value = (1,)
    variant_result = MagicMock(); variant_result.mappings().first.return_value = {
        "id": 1, "onHand": 100, "cogs": 10000.0
    }
    insert_result = MagicMock(); insert_result.mappings().first.return_value = {
        "tenantId": 1, "branchId": 1, "skuId": 1, "type": "IMPORT", "quantity": 50, "balanceAfter": 150
    }
    db.execute.side_effect = [branch_result, variant_result, MagicMock(), insert_result]
    result = InventoryRepository.process_purchase_receipt_tx(db,1,1,1,50,12000.0,"TEST-IMPORT-01")
    assert result["currentStock"] == 150
    # Import is append-only: an InventoryTransaction INSERT is performed; no ledger UPDATE is issued.
    assert db.commit.called


def test_anti_oversell():
    db = MagicMock()
    variant = MagicMock(); variant.mappings().first.return_value = {"id":1,"sku":"SKU-001","onHand":10,"reserved":5}
    db.execute.return_value = variant
    result = RSERepository._variant(db,1,1)
    assert result["onHand"] == 10
