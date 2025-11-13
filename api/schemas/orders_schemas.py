from pydantic import BaseModel

class OrderCreate(BaseModel):
    customer_name: str
    restaurant_id: int
    item: str
    quantity: int

class Order(OrderCreate):
    id: int
