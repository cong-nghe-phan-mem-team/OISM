"""Read-only check of the required OISM3 tables/columns in Supabase/PostgreSQL."""
from sqlalchemy import text
from app.database import engine, is_sqlite

REQUIRED = {
    "tenants": {"tenantId", "name", "status"},
    "users": {"userId", "email", "phone", "passwordHash", "fullName", "tenantId", "roleId", "createdAt"},
    "roles": {"roleId", "roleName"},
    "branches": {"branchId", "branchName", "isActive", "tenantId"},
    "Product": {"id", "tenantId", "title"},
    "ProductVariant": {"id", "tenantId", "productId", "sku", "retailPrice", "onHand", "reserved", "cogs", "reorderLevel"},
    "Order": {"orderId", "tenantId", "branchId", "status", "totalAmount", "discount", "finalAmount", "paymentMethod"},
    "OrderItem": {"id", "tenantId", "orderId", "skuId", "quantity", "unitPrice", "subTotal"},
    "InventoryTransaction": {"id", "tenantId", "branchId", "skuId", "type", "quantity", "balanceAfter", "referenceId", "createdAt"},
    "WebhookLog": {"id", "tenantId", "platform", "eventType", "payload", "status", "createdAt"},
    "Notification": {"id", "tenantId", "message", "status", "createdAt"},
}

if is_sqlite():
    raise SystemExit("Set DATABASE_URL to your Supabase PostgreSQL connection string before running this check.")

with engine.connect() as db:
    rows=db.execute(text('''SELECT table_name,column_name FROM information_schema.columns
        WHERE table_schema='public' ORDER BY table_name,ordinal_position''')).all()

actual={}
for table,column in rows:
    actual.setdefault(table,set()).add(column)

errors=[]
for table,columns in REQUIRED.items():
    if table not in actual:
        errors.append(f"Missing table: {table}")
        continue
    for column in sorted(columns-actual[table]):
        errors.append(f"Missing column: {table}.{column}")

if errors:
    print("SCHEMA_CHECK_FAILED")
    print("\n".join(errors))
    raise SystemExit(1)
print("SCHEMA_CHECK_OK")
print("All required OISM3 tables/columns were found.")
