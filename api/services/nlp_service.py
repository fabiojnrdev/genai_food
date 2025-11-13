import random
from api.services.recommender import get_recommendation

def process_message(message):
    if 'pedido' in message.lower():
        return "Seu pedido está a caminho!"
    elif 'recomenda' or 'restaurante' in message.lower():
        return get_recommendation()
    else:
        respostas = [
            "Olá! Como posso lhe ajudar hoje?",
            "Desculpe, não entendi sua solicitação. Poderia repetir?",
            "Posso verificar seu pedido ou recomendar algo para voce.",
            "Quer uma recomendação personalizada?" 
        ]
        return random.choice(respostas)
    