import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DB = Path(__file__).resolve().parents[1] / 'e2e_test.db'
if DB.exists():
    DB.unlink()
os.environ['DATABASE_URL'] = f'sqlite:///{DB}'
os.environ['JWT_SECRET'] = 'e2e-secret'

# The execution container used for static validation does not ship passlib.
# Install requirements in the real project; this fallback is only for this local
# integration harness and is never part of the application.
try:
    import passlib.hash  # type: ignore
except ModuleNotFoundError:
    import hashlib, types
    class _FakeBcrypt:
        @staticmethod
        def hash(password):
            return 'TEST$' + hashlib.sha256(password.encode()).hexdigest()
        @staticmethod
        def verify(password, stored):
            return stored == _FakeBcrypt.hash(password)
    _passlib = types.ModuleType('passlib')
    _hash = types.ModuleType('passlib.hash')
    _hash.bcrypt = _FakeBcrypt
    _passlib.hash = _hash
    sys.modules['passlib'] = _passlib
    sys.modules['passlib.hash'] = _hash

from app.main import app  # noqa: E402
from app.database import engine  # noqa: E402

# Initialize schema using the same local schema shipped with the project.
schema = Path(__file__).resolve().parents[1] / 'local_schema.sql'
with engine.begin() as conn:
    for statement in schema.read_text(encoding='utf-8').split(';'):
        statement = statement.strip()
        if statement:
            conn.exec_driver_sql(statement)

from fastapi.testclient import TestClient  # noqa: E402
client = TestClient(app)


def check(resp, code=200):
    assert resp.status_code == code, f'{resp.status_code}: {resp.text}'
    return resp.json()

# 1-2 Database/Auth
check(client.get('/health'))
r = check(client.post('/auth/register', json={
    'tenantName': 'E2E Tenant',
    'ownerEmail': 'e2e@example.com',
    'password': 'secret123',
    'fullName': 'E2E Owner',
    'phone': '0900000000',
}))
assert r['data']['tenantId'] == 1
login = check(client.post('/auth/login', json={'email': 'e2e@example.com', 'password': 'secret123'}))
token = login['access_token']
headers = {'Authorization': f'Bearer {token}'}
me = check(client.get('/auth/me', headers=headers))
branch_id = me['branchId']
assert branch_id == 1

# 3 Product
p = check(client.post('/products', headers=headers, json={
    'title': 'E2E Product',
    'variants': [{'sku': 'SKU-E2E', 'retailPrice': '100000', 'wholesalePrice': '80000'}],
}))
variant_id = p['data']['variants'][0]['id']

# 4 Inventory/COGS
receipt = check(client.post('/inventory/receipts', headers=headers, json={
    'skuId': 'SKU-E2E', 'branchId': branch_id, 'importQuantity': 10,
    'importUnitPrice': '50000', 'referenceId': 'E2E-IMPORT'
}))
assert receipt['data']['currentStock'] == 10
assert abs(receipt['data']['updatedCogs'] - 50000) < 0.01
check(client.post(f"/cost/receipts/{receipt['data']['ledgerEntry']['id']}/confirm", headers=headers))

# 5 RSE
stock = check(client.get('/rse/available-stock', headers=headers, params={'sku_id': 'SKU-E2E', 'branch_id': branch_id}))
assert stock['available_stock'] == 10

# 6 Order + reservation/confirmation/cancellation
order = check(client.post('/orders', headers=headers, json={
    'branch_id': branch_id, 'sales_channel': 'web',
    'items': [{'sku_id': 'SKU-E2E', 'quantity': 2, 'unit_price': '100000'}]
}))
order_id = order['order_id']
check(client.post(f'/orders/{order_id}/reserve', headers=headers))
stock = check(client.get('/rse/available-stock', headers=headers, params={'sku_id': 'SKU-E2E', 'branch_id': branch_id}))
assert stock['available_stock'] == 8
check(client.post(f'/orders/{order_id}/confirm', headers=headers))
check(client.post(f'/orders/{order_id}/cancel', headers=headers))
stock = check(client.get('/rse/available-stock', headers=headers, params={'sku_id': 'SKU-E2E', 'branch_id': branch_id}))
assert stock['available_stock'] == 10

# 7 POS
pos = check(client.post('/pos/checkout', headers=headers, json={
    'items': [{'sku': 'SKU-E2E', 'quantity': 3, 'price': '100000'}],
    'discount': '10000', 'payment_method': 'Cash'
}))
assert pos['receipt']['order']['type'] == 'POS'
stock = check(client.get('/rse/available-stock', headers=headers, params={'sku_id': 'SKU-E2E', 'branch_id': branch_id}))
assert stock['available_stock'] == 7

# 8 Report
rev = check(client.get('/reports/revenue', headers=headers))
assert rev['data']['total_revenue'] == 290000
inv = check(client.get('/reports/inventory', headers=headers))
assert inv['data'][0]['available'] == 7

# 9 Webhook
wh = check(client.post('/system/webhook/receive', headers=headers, json={
    'platform': 'Test', 'event_type': 'ORDER_UPDATED', 'payload': {'orderId': order_id}
}))
assert wh['data']['status'] == 'Processed'
notifications = check(client.get('/system/notifications', headers=headers))
assert len(notifications['data']) >= 1

print('E2E_LOCAL_OK')
print('tenantId=', me['tenantId'], 'branchId=', branch_id, 'variantId=', variant_id, 'orderId=', order_id)
print('revenue=', rev['data']['total_revenue'], 'available=', inv['data'][0]['available'])
