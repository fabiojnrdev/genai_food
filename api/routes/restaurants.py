from fastapi import APIRouter, HTTPException
from typing import List
from api.schemas.restaurants_schemas import Restaurant, RestaurantCreate

router = APIRouter(prefix="/restaurants", tags=["restaurants"])
restaurants_db = [
    {"id": 1, "nome": "Pizzaria Saborosa", "categoria": "Pizza", "nota_media": 4.7},
    {"id": 2, "nome": "Veg & Go", "categoria": "Comida Vegana", "nota_media": 4.8},
    {"id": 3, "nome": "Tô com Fome Burgers", "categoria": "Hambúrguer", "nota_media": 4.5},
    {"id": 4, "nome": "Restaurante Toca da Fome", "categoria": "Marmita", "nota_media": 4.5},
    {"id": 5, "nome": "Sushi Master", "categoria": "Comida Japonesa", "nota_media": 4.9},
    {"id": 6, "nome": "Churrascaria Boi na Brasa", "categoria": "Churrasco", "nota_media": 4.6},
    {"id": 7, "nome": "La Pasta", "categoria": "Comida Italiana", "nota_media": 4.4},
    {"id": 8, "nome": "Café do Bairro", "categoria": "Café", "nota_media": 4.3},
    {"id": 9, "nome": "Delícias do Mar", "categoria": "Frutos do Mar", "nota_media": 4.7},
]
@router.get("/", response_model=List[Restaurant])
def list_restaurants():
    return restaurants_db
@router.post("/{restaurant_id}", response_model=Restaurant)
def get_restaurant(restaurant_id: int):
    for restaurant in restaurants_db:
        if restaurant["id"] == restaurant_id:
            return restaurant
    raise HTTPException(status_code=404, detail="Restaurante não encontrado")
@router.post("/", response_model=Restaurant)
def add_restaurant(restaurant: RestaurantCreate):
    new_restaurant = {
        "id": len(restaurants_db) + 1,
        **restaurant.dict()
    }
    restaurants_db.append(new_restaurant)
    return new_restaurant