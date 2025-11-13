from pydantic import BaseModel

class Restaurant(BaseModel):
    id: int
    nome: str
    categoria: str
    nota_media: float
class RestaurantCreate(BaseModel):
    nome: str
    categoria: str
    nota_media: float
