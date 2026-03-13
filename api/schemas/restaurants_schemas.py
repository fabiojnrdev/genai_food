from pydantic import BaseModel, Field


class RestaurantBase(BaseModel):
    name: str
    category: str
    rating: float = Field(..., ge=0.0, le=5.0)
    address: str
    phone: str


class RestaurantCreate(RestaurantBase):
    pass


class Restaurant(RestaurantBase):
    id: int

    class Config:
        from_attributes = True