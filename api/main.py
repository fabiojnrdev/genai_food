from fastapi import FastAPI

from api.routes import chat, restaurants, orders

app = FastAPI(
    title="Food Delivery Chatbot API",
    description="Agente inteligente para recomendação e atendimento em delivery de comida.",
    version="1.0.0",
)

app.include_router(chat.router)
app.include_router(restaurants.router)
app.include_router(orders.router)


@app.get("/", tags=["health"])
def root():
    # era `return {"Bem-vindo..."}` — um set Python, não serializável como JSON
    return {"message": "Bem-vindo ao Food Delivery Chatbot API!"}