from pydantic import BaseModel, Field, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)