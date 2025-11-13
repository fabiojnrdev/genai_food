import json
import random
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'restaurants.json')

def get_recommendation(message: str = "") -> str:
    
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        restaurants = json.load(file)

    msg = message.lower() if message else ""
    
    categorias = set(r["category"].lower() for r in restaurants)

    for categoria in categorias:
        if categoria in msg:
            recomendados = [r for r in restaurants if r["category"].lower() == categoria]
            if recomendados:
                choice = random.choice(recomendados)
                return (
                    f"Recomendo o restaurante '{choice['name']}' \n"
                    f"Categoria: {choice['category']}, {choice['rating']}\n "
                    f"Endereço: {choice['address']}, "
                    f"Telefone: {choice['phone']}"
                )
    choice = random.choice(restaurants)
    return (
        f"Você poderia gostar de experimentar o **{choice['name']}** 😋\n"
        f"Categoria: {choice['category']} — ⭐ {choice['rating']}"
    )