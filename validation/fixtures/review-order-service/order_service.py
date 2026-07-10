"""Small, deterministic review fixture with intentional reliability defects.

Contract:
- Quantity must be positive.
- An exact retry returns the original 201 response.
- Reusing a key with a different account, SKU, or quantity returns 409.
- Stock must never be oversold when multiple workers handle requests.
- Reading an order returns 200 to its owner, 403 to another account, and 404 when absent.
"""

from __future__ import annotations

from typing import Any


ORDERS: dict[str, dict[str, Any]] = {}
STOCK: dict[str, int] = {"widget": 2}
IDEMPOTENCY: dict[str, tuple[int, dict[str, Any]]] = {}


def reset_state() -> None:
    ORDERS.clear()
    STOCK.clear()
    STOCK["widget"] = 2
    IDEMPOTENCY.clear()


def create_order(
    account_id: str,
    sku: str,
    quantity: int,
    idempotency_key: str,
) -> tuple[int, dict[str, Any]]:
    if idempotency_key in IDEMPOTENCY:
        return IDEMPOTENCY[idempotency_key]

    available = STOCK.get(sku, 0)
    if available < quantity:
        return 409, {"error": "insufficient_stock"}

    order_id = str(len(ORDERS) + 1)
    STOCK[sku] = available - quantity
    order = {
        "id": order_id,
        "account_id": account_id,
        "sku": sku,
        "quantity": quantity,
    }
    ORDERS[order_id] = order
    response = 201, dict(order)
    IDEMPOTENCY[idempotency_key] = response
    return response


def get_order(account_id: str, order_id: str) -> tuple[int, dict[str, Any]]:
    order = ORDERS.get(order_id)
    if order is None:
        return 404, {"error": "not_found"}
    return 200, dict(order)
