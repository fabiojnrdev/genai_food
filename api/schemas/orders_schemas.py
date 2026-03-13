from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_name: str
    restaurant_id: int = Field(..., gt=0)
    item: str
    quantity: int = Field(..., gt=0, description="Deve ser maior que zero")


class Order(OrderCreate):
    id: int