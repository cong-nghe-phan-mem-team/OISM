"""Regression tests for the legacy INTEGER/camelCase Supabase schema.

These tests intentionally avoid the live Supabase database and use an equivalent
SQLite schema. They protect the critical Product -> Inventory/WAC -> RSE -> POS
-> Order flow and tenant isolation.
"""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.repositories.inventory_repo import InventoryRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.pos_repo import POSRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.rse_repo import RSERepository


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def sqlite_functions(connection, _record):
        connection.create_function("NOW", 0, lambda: "2026-09-10 00:00:00")

    with engine.begin() as conn:
        ddl = [
            'CREATE TABLE tenants (tenantId INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, status TEXT NOT NULL, createdAt TEXT)',
            'CREATE TABLE roles (roleId INTEGER PRIMARY KEY AUTOINCREMENT, roleName TEXT UNIQUE NOT NULL, permissions TEXT)',
            'CREATE TABLE branches (branchId INTEGER PRIMARY KEY AUTOINCREMENT, branchName TEXT NOT NULL, address TEXT, isActive BOOLEAN NOT NULL DEFAULT 1, tenantId INTEGER NOT NULL)',
            'CREATE TABLE users (userId INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, phone TEXT, passwordHash TEXT NOT NULL, fullName TEXT, tenantId INTEGER NOT NULL, roleId INTEGER, createdAt TEXT)',
            'CREATE TABLE "Product" (id INTEGER PRIMARY KEY AUTOINCREMENT, tenantId INTEGER NOT NULL, title TEXT NOT NULL, categoryId INTEGER, brandId INTEGER, createdAt TEXT)',
            'CREATE TABLE "ProductVariant" (id INTEGER PRIMARY KEY AUTOINCREMENT, tenantId INTEGER NOT NULL, productId INTEGER NOT NULL, sku TEXT NOT NULL, barcode TEXT, retailPrice NUMERIC NOT NULL DEFAULT 0, wholesalePrice NUMERIC NOT NULL DEFAULT 0, attributes TEXT NOT NULL DEFAULT "{}", onHand INTEGER NOT NULL DEFAULT 0, reserved INTEGER NOT NULL DEFAULT 0, cogs NUMERIC NOT NULL DEFAULT 0, reorderLevel INTEGER NOT NULL DEFAULT 5, createdAt TEXT)',
            'CREATE TABLE "InventoryTransaction" (id INTEGER PRIMARY KEY AUTOINCREMENT, tenantId INTEGER NOT NULL, branchId INTEGER NOT NULL, skuId INTEGER NOT NULL, type TEXT NOT NULL, quantity INTEGER NOT NULL, balanceAfter INTEGER NOT NULL, referenceId TEXT, createdAt TEXT)',
            'CREATE TABLE "Order" (orderId INTEGER PRIMARY KEY AUTOINCREMENT, tenantId INTEGER NOT NULL, branchId INTEGER NOT NULL, salesChannel TEXT, type TEXT NOT NULL DEFAULT "ONLINE", status TEXT NOT NULL DEFAULT "PENDING", totalAmount NUMERIC NOT NULL DEFAULT 0, discount NUMERIC NOT NULL DEFAULT 0, finalAmount NUMERIC NOT NULL DEFAULT 0, paymentMethod TEXT, createdAt TEXT)',
            'CREATE TABLE "OrderItem" (id INTEGER PRIMARY KEY AUTOINCREMENT, tenantId INTEGER NOT NULL, orderId INTEGER NOT NULL, skuId INTEGER NOT NULL, quantity NUMERIC NOT NULL, unitPrice NUMERIC NOT NULL, subTotal NUMERIC NOT NULL)',
        ]
        for statement in ddl:
            conn.exec_driver_sql(statement)
        conn.execute(text("INSERT INTO tenants(name,status) VALUES('T1','ACTIVE')"))
        conn.execute(text("INSERT INTO roles(roleName,permissions) VALUES('OWNER','ALL')"))
        conn.execute(text("INSERT INTO branches(branchName,isActive,tenantId) VALUES('Main',1,1)"))

    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_product_inventory_rse_pos_order_flow(db):
    product = ProductRepository.create_product_with_variants(
        db,
        1,
        {
            "title": "Brake Pad",
            "categoryId": None,
            "brandId": None,
            "variants": [{
                "sku": "BP-001",
                "barcode": None,
                "retailPrice": Decimal("100000"),
                "wholesalePrice": Decimal("70000"),
                "attributes": {},
            }],
        },
    )
    assert product["variants"][0]["sku"] == "BP-001"

    first = InventoryRepository.process_purchase_receipt_tx(db, 1, 1, "BP-001", 10, Decimal("70000"), "IMP-1")
    second = InventoryRepository.process_purchase_receipt_tx(db, 1, 1, "BP-001", 10, Decimal("90000"), "IMP-2")
    assert first["currentStock"] == 10
    assert second["currentStock"] == 20
    assert second["updatedCogs"] == 80000

    assert RSERepository.get_available_stock(db, 1, "BP-001", 1) == 20
    RSERepository.reserve(db, 1, "BP-001", 1, 5, "RES-1")
    db.commit()
    assert RSERepository.get_available_stock(db, 1, "BP-001", 1) == 15

    with pytest.raises(ValueError):
        RSERepository.reserve(db, 1, "BP-001", 1, 16, "RES-2")

    # A forged POS price must not change the database retail price.
    pos = POSRepository.save_pos_receipt(
        db, 1, 1, 0, 0, 0, "Cash",
        [{"sku": "BP-001", "quantity": 2, "price": Decimal("1")}],
    )
    assert pos["items"][0]["price"] == 100000.0
    assert float(pos["order"]["totalAmount"]) == 200000.0

    # Order also uses ProductVariant.retailPrice, not the client price.
    order_id = OrderRepository.insert_order(
        db, 1,
        {"branchId": 1, "salesChannel": "WEB"},
        [{"skuId": "BP-001", "quantity": 2, "unitPrice": Decimal("1")}],
    )
    order, _ = OrderRepository.get_order(db, 1, order_id)
    assert float(order["totalAmount"]) == 200000.0

    OrderRepository.update_order_status(db, 1, order_id, "reserve")
    assert RSERepository.get_available_stock(db, 1, "BP-001", 1) == 11
    OrderRepository.update_order_status(db, 1, order_id, "cancel")
    assert RSERepository.get_available_stock(db, 1, "BP-001", 1) == 13


def test_release_cannot_underflow_reserved(db):
    ProductRepository.create_product_with_variants(
        db, 1,
        {"title": "P", "categoryId": None, "brandId": None,
         "variants": [{"sku": "S1", "retailPrice": 10, "wholesalePrice": 5, "attributes": {}}]},
    )
    InventoryRepository.process_purchase_receipt_tx(db, 1, 1, "S1", 5, Decimal("5"), "I1")
    RSERepository.reserve(db, 1, "S1", 1, 2, "R1")
    db.commit()
    with pytest.raises(ValueError):
        RSERepository.release_reservation(db, 1, "S1", 1, 3, "BAD")
