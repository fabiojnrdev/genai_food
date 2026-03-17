from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.database import get_db
from api.schemas.orders_schemas import Order, OrderCreate
from api.services import orders_service
from api.services.auth_service import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=Order, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return orders_service.create_order(db, order)


@router.get("/", response_model=List[Order])
def list_orders(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return orders_service.list_orders(db)


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_order = orders_service.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return db_order


@router.delete("/{order_id}", status_code=200)
def delete_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_order = orders_service.delete_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return {"message": f"Pedido #{order_id} removido com sucesso"}