from fastapi import APIRouter, HTTPException
from typing import List

from api.schemas.orders_schemas import Order, OrderCreate

router = APIRouter(prefix="/orders", tags=["orders"])

# Em produção isso seria um banco de dados. Mantido em memória conforme o design original.
orders_db: List[Order] = []


@router.post("/", response_model=Order, status_code=201)
def create_order(order: OrderCreate):
    new_order = Order(id=len(orders_db) + 1, **order.model_dump())
    orders_db.append(new_order)
    return new_order


@router.get("/", response_model=List[Order])
def list_orders():
    return orders_db


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int):
    for order in orders_db:
        if order.id == order_id:
            return order
    raise HTTPException(status_code=404, detail="Pedido não encontrado")


@router.delete("/{order_id}", status_code=200)
def delete_order(order_id: int):
    for order in orders_db:
        if order.id == order_id:
            orders_db.remove(order)
            return {"message": f"Pedido #{order_id} removido com sucesso"}
    raise HTTPException(status_code=404, detail="Pedido não encontrado")