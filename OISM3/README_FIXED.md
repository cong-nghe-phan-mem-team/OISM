# OISM3 - Legacy Supabase Schema Compatible Build

This build targets the INTEGER/camelCase Supabase schema currently used by OISM:
`users`, `tenants`, `roles`, `branches`, `Product`, `ProductVariant`, `InventoryTransaction`, `Order`, `OrderItem`, `Notification`, and `WebhookLog`.

It does **not** migrate the database to UUID/snake_case.

## Main fixes

1. **Database**
   - Kept the existing legacy schema unchanged.
   - Tenant/branch filters remain enforced in repository queries.
   - Purchase WAC calculation uses a PostgreSQL row lock (`FOR UPDATE`) to prevent concurrent lost updates.

2. **Auth**
   - Fixed `/auth/login` using the wrong variable (`data` -> `request`).
   - Fixed `/auth/register` passing a Pydantic model where a dict was expected (`request.model_dump()`).
   - Login stores the returned user object in browser localStorage.
   - Existing legacy `userId`, `tenantId`, `roleId`, and `branchId` claims are preserved.

3. **Product**
   - Product creation/listing remains compatible with the current schema.
   - Frontend now supports multiple variants and correct Remove buttons.

4. **Inventory / COGS**
   - WAC calculation remains weighted-average.
   - Inventory transactions are append-only.
   - PostgreSQL row locking was added to the SKU read used by WAC.

5. **RSE**
   - Reservation remains atomic and tenant-scoped.
   - Releasing more reserved stock than exists is rejected instead of silently clamping to zero.

6. **Order**
   - Client-provided `unit_price` is now optional/backward compatible.
   - Backend uses `ProductVariant.retailPrice` as the authoritative price.

7. **POS**
   - Client-provided `price` is optional/backward compatible.
   - Backend uses `ProductVariant.retailPrice` as the authoritative price.
   - POS stock update uses a locked SKU row on PostgreSQL to reduce concurrent oversell risk.

8. **Frontend**
   - API URL uses the current browser origin instead of hard-coded `127.0.0.1`.
   - POS and Order pages preload retail prices from Product data and display them as read-only.

## Important current-schema limitation

`ProductVariant.onHand` and `ProductVariant.reserved` are SKU-level counters, while `InventoryTransaction` has `branchId`. Therefore this legacy schema cannot represent independent stock quantities per branch. The application validates the selected branch but does not invent a branch-specific stock table.

For true per-branch inventory, add a dedicated branch-stock table in a separate schema migration after the current system is stable.

## Environment

The `.env` included in this build contains placeholders only. Copy your existing local `.env` values into it; do not commit database passwords.

## Run

```powershell
uvicorn app.main:app --reload --log-level debug
```

Open:

`http://127.0.0.1:8000/`

## Tests

The included regression tests use an equivalent local SQLite schema and do not modify Supabase.

```powershell
pytest -q
```

The tested flow covers:

`Auth -> Product -> Inventory/WAC -> RSE -> POS -> Order -> Reports/Webhook`

plus negative tests for overselling, duplicate SKU, invalid credentials, and reservation underflow.
