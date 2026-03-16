import json

from fastapi import APIRouter, HTTPException
from typing import List

from api.config import settings
from api.schemas.restaurants_schemas import Restaurant, RestaurantCreate

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def _load_restaurants() -> list[dict]:
    with settings.restaurants_data_path.open(encoding="utf-8") as f:
        return json.load(f)


def _save_restaurants(data: list[dict]) -> None:
    with settings.restaurants_data_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/", response_model=List[Restaurant])
def list_restaurants():
    return _load_restaurants()


@router.get("/{restaurant_id}", response_model=Restaurant)  # era POST — corrigido para GET
def get_restaurant(restaurant_id: int):
    restaurants = _load_restaurants()
    for restaurant in restaurants:
        if restaurant["id"] == restaurant_id:
            return restaurant
    raise HTTPException(status_code=404, detail="Restaurante não encontrado")


@router.post("/", response_model=Restaurant, status_code=201)
def add_restaurant(restaurant: RestaurantCreate):
    restaurants = _load_restaurants()
    new_id = max((r["id"] for r in restaurants), default=0) + 1
    new_restaurant = {"id": new_id, **restaurant.model_dump()}
    restaurants.append(new_restaurant)
    _save_restaurants(restaurants)
    return new_restaurant