import random
from api.services.recommender import get_recommendation

def process_user_message(message: str) -> str:
    if not message:
        return "Desculpe, não entendi sua mensagem."

    msg = message.lower()

    if "pedido" in msg:
        return "Seu pedido está a caminho!"
    elif "recomenda" in msg or "restaurante" in msg:
        return get_recommendation(message)

    respostas = [
        "Olá! Como posso lhe ajudar hoje?",
        "Desculpe, não entendi sua solicitação. Poderia repetir?",
        "Posso verificar seu pedido ou recomendar algo para você.",
        "Quer uma recomendação personalizada?"
    ]

    return random.choice(respostas)
