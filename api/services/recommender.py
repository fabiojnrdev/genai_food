import json, random

def get_recommendation():
    with open("data/restaurants.json", "r", encoding="utf-8") as f:
        restaurants = json.load(f)
    choice = random.choice(restaurants)
    return f"Que tal pedir no {choice['name']}? {choice['category']} com nota {choice['rating']} ⭐"
