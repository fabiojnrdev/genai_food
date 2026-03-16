import json
import random

from api.config import settings


def _load_restaurants() -> list[dict]:
    with settings.restaurants_data_path.open(encoding="utf-8") as f:
        return json.load(f)


def get_recommendation(message: str = "") -> str:
    restaurants = _load_restaurants()
    msg = message.lower().strip()

    # Tenta encontrar restaurantes que correspondam à categoria mencionada
    if msg:
        matched = [
            r for r in restaurants
            if r["category"].lower() in msg
        ]
        if matched:
            choice = random.choice(matched)
            return (
                f"Recomendo o restaurante **{choice['name']}** 😋\n"
                f"Categoria: {choice['category']} — ⭐ {choice['rating']}\n"
                f"Endereço: {choice['address']}\n"
                f"Telefone: {choice['phone']}"
            )

    # Fallback: recomendação aleatória
    choice = random.choice(restaurants)
    return (
        f"Que tal experimentar o **{choice['name']}**? 😋\n"
        f"Categoria: {choice['category']} — ⭐ {choice['rating']}\n"
        f"Endereço: {choice['address']}\n"
        f"Telefone: {choice['phone']}"
    )