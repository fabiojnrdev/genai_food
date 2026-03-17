"""
Serviço de NLP com HuggingFace Inference API.

Estratégia:
- Classificação zero-shot via joeddav/xlm-roberta-large-xnli
- Sem necessidade de dataset de treino — as intenções são passadas como labels
- Fallback automático para keyword-based se a API estiver indisponível ou
  a key não estiver configurada (dev sem internet, testes, etc.)

Fluxo:
    mensagem → _classify_intent_hf() → intenção → resposta
                    ↓ falha
              _detect_intent_keywords() → intenção → resposta
"""

import requests

from api.config import settings
from api.logger import get_logger
from api.services.recommender import get_recommendation

logger = get_logger(__name__)

# Labels enviados ao modelo — devem ser autoexplicativos em português
_INTENT_LABELS = [
    "verificar status de pedido",
    "recomendar restaurante",
    "saudação",
    "ajuda com o sistema",
]

# Mapeamento do label retornado pelo modelo para a intenção interna
_LABEL_TO_INTENT = {
    "verificar status de pedido": "order_status",
    "recomendar restaurante":     "recommendation",
    "saudação":                   "greeting",
    "ajuda com o sistema":        "help",
}

# Fallback keyword-based (mantido para resiliência)
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "order_status":   ["pedido", "rastrear", "rastreio", "onde está", "status", "entrega"],
    "recommendation": ["recomenda", "sugest", "restaurante", "onde comer", "quero comer", "com fome", "comer"],
    "greeting":       ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hey"],
    "help":           ["ajuda", "help", "o que você faz", "como funciona", "menu"],
}


# ---------------------------------------------------------------------------
# Classificação via HuggingFace
# ---------------------------------------------------------------------------

def _classify_intent_hf(message: str) -> str | None:
    """
    Chama a Inference API e retorna a intenção de maior score.
    Retorna None em caso de falha para acionar o fallback.
    """
    if not settings.hf_api_key:
        logger.debug("HF_API_KEY não configurada — usando fallback keyword-based")
        return None

    try:
        response = requests.post(
            settings.hf_api_url,
            headers={"Authorization": f"Bearer {settings.hf_api_key}"},
            json={
                "inputs": message,
                "parameters": {"candidate_labels": _INTENT_LABELS},
            },
            timeout=15,
        )

        # Modelo ainda carregando no servidor HuggingFace (cold start)
        if response.status_code == 503:
            logger.warning("Modelo HuggingFace ainda carregando, usando fallback")
            return None

        response.raise_for_status()
        data = response.json()

        # Formato esperado: {"labels": [...], "scores": [...]}
        top_label = data["labels"][0]
        top_score = data["scores"][0]

        logger.debug(
            f"HF classificou '{message[:40]}' como '{top_label}' (score={top_score:.3f})"
        )

        # Score baixo = modelo incerto → fallback
        if top_score < 0.4:
            logger.debug(f"Score {top_score:.3f} abaixo do limiar — usando fallback")
            return None

        return _LABEL_TO_INTENT.get(top_label)

    except requests.exceptions.Timeout:
        logger.warning("Timeout na Inference API — usando fallback keyword-based")
        return None
    except Exception as exc:
        logger.warning(f"Erro na Inference API: {exc} — usando fallback keyword-based")
        return None


# ---------------------------------------------------------------------------
# Fallback keyword-based
# ---------------------------------------------------------------------------

def _detect_intent_keywords(message: str) -> str:
    msg = message.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return "unknown"


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def _detect_intent(message: str) -> str:
    """Tenta HuggingFace primeiro, cai no fallback se necessário."""
    intent = _classify_intent_hf(message)
    if intent is None:
        intent = _detect_intent_keywords(message)
    return intent


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