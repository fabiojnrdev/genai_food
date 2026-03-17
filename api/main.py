from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.database import init_db
from api.routes import auth, chat, restaurants, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Food Delivery Chatbot API",
    description="Agente inteligente para recomendação e atendimento em delivery de comida.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(restaurants.router)
app.include_router(orders.router)


@app.get("/", tags=["health"])
def root():
    return {"message": "Bem-vindo ao Food Delivery Chatbot API!"}