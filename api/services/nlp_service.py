from api.services.recommender import get_recommendation

# Mapeamento de intenções por palavras-chave
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "order_status": ["pedido", "rastrear", "rastreio", "onde está", "status", "entrega"],
    "recommendation": ["recomenda", "sugest", "restaurante", "onde comer", "quero comer", "com fome"],
    "greeting": ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hey"],
    "help": ["ajuda", "help", "o que você faz", "como funciona", "menu"],
}


def _detect_intent(message: str) -> str:
    msg = message.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return "unknown"


def process_user_message(message: str) -> str:
    if not message or not message.strip():
        return "Não recebi nenhuma mensagem. Como posso ajudar?"

    intent = _detect_intent(message)

    if intent == "order_status":
        return (
            "Seu pedido está sendo preparado e em breve estará a caminho! 🛵\n"
            "Para rastrear em tempo real, informe o número do seu pedido."
        )

    if intent == "recommendation":
        return get_recommendation(message)

    if intent == "greeting":
        return (
            "Olá! Seja bem-vindo ao Food Delivery 🍔\n"
            "Posso te ajudar a encontrar restaurantes, acompanhar pedidos ou fazer recomendações. "
            "O que você precisa?"
        )

    if intent == "help":
        return (
            "Posso te ajudar com:\n"
            "• 🍕 Recomendar restaurantes\n"
            "• 📦 Verificar status de pedidos\n"
            "• 🗂️ Listar categorias disponíveis\n\n"
            "É só me dizer o que você precisa!"
        )

    return (
        "Não entendi exatamente o que você precisa. 😕\n"
        "Tente me dizer se quer uma recomendação de restaurante ou verificar um pedido."
    )