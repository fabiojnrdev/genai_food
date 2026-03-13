"""
Testes unitários para os serviços de modelo/NLP.

Estratégia:
- recommender: mockamos _load_restaurants para controlar os dados
  e usamos random.seed para tornar os testes determinísticos.
- nlp_service: mockamos get_recommendation para isolar a detecção
  de intenção da lógica de recomendação.
- _detect_intent é testada diretamente por ser a lógica central do serviço.
"""

import random
import pytest
from unittest.mock import patch

from api.services.nlp_service import process_user_message, _detect_intent
from api.services.recommender import get_recommendation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_RESTAURANTS = [
    {
        "id": 1,
        "name": "Pizzaria Saborosa",
        "category": "Pizza",
        "rating": 4.7,
        "address": "Rua das Flores, 123",
        "phone": "(86) 99999-0001",
    },
    {
        "id": 2,
        "name": "Sushi Master",
        "category": "Comida Japonesa",
        "rating": 4.9,
        "address": "Av. Japão, 654",
        "phone": "(86) 99999-0005",
    },
    {
        "id": 3,
        "name": "Veg & Go",
        "category": "Comida Vegana",
        "rating": 4.8,
        "address": "Av. Verde, 456",
        "phone": "(86) 99999-0002",
    },
]


# ---------------------------------------------------------------------------
# _detect_intent
# ---------------------------------------------------------------------------

class TestDetectIntent:
    """Testa o mapeamento de intenções diretamente, sem passar pela resposta."""

    @pytest.mark.parametrize("message,expected", [
        ("cadê meu pedido?",           "order_status"),
        ("quero rastrear minha entrega", "order_status"),
        ("qual o status do pedido",    "order_status"),
        ("me recomenda um restaurante","recommendation"),
        ("onde posso comer hoje?",     "recommendation"),
        ("estou com fome",             "recommendation"),
        ("oi tudo bem",                "greeting"),
        ("bom dia!",                   "greeting"),
        ("boa noite",                  "greeting"),
        ("preciso de ajuda",           "help"),
        ("como funciona o app?",       "help"),
        ("xkcd 1234 ???",              "unknown"),
        ("",                           "unknown"),
    ])
    def test_intent_detection(self, message, expected):
        assert _detect_intent(message) == expected

    def test_is_case_insensitive(self):
        assert _detect_intent("OI TUDO BEM") == "greeting"
        assert _detect_intent("PEDIDO") == "order_status"


# ---------------------------------------------------------------------------
# process_user_message — respostas por intenção
# ---------------------------------------------------------------------------

class TestProcessUserMessage:
    def test_empty_message_returns_fallback(self):
        result = process_user_message("")
        assert "não recebi" in result.lower()

    def test_whitespace_only_returns_fallback(self):
        result = process_user_message("   ")
        assert "não recebi" in result.lower()

    def test_greeting_returns_welcome_message(self):
        result = process_user_message("oi")
        assert "bem-vindo" in result.lower()

    def test_help_returns_capabilities_list(self):
        result = process_user_message("preciso de ajuda")
        assert "recomendar" in result.lower()
        assert "pedido" in result.lower()

    def test_order_status_returns_status_message(self):
        result = process_user_message("onde está meu pedido?")
        assert "caminho" in result.lower() or "preparado" in result.lower()

    def test_unknown_intent_returns_clarification_request(self):
        result = process_user_message("xkcd 9999 ???")
        assert "não entendi" in result.lower()

    @patch("api.services.nlp_service.get_recommendation", return_value="Recomendo a Pizzaria X")
    def test_recommendation_intent_calls_recommender(self, mock_rec):
        result = process_user_message("me recomenda algo")
        mock_rec.assert_called_once_with("me recomenda algo")
        assert result == "Recomendo a Pizzaria X"

    @patch("api.services.nlp_service.get_recommendation", return_value="Mock")
    def test_recommendation_passes_original_message_to_recommender(self, mock_rec):
        """Garante que a mensagem original (não lowercased) chega ao recommender."""
        process_user_message("Quero comer Pizza")
        mock_rec.assert_called_once_with("Quero comer Pizza")


# ---------------------------------------------------------------------------
# get_recommendation
# ---------------------------------------------------------------------------

class TestGetRecommendation:
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_returns_non_empty_string(self, _mock):
        result = get_recommendation("quero comer algo")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_contains_restaurant_name(self, _mock):
        names = {r["name"] for r in MOCK_RESTAURANTS}
        result = get_recommendation("")
        assert any(name in result for name in names)

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_category_match_returns_matching_restaurant(self, _mock):
        """Quando a mensagem contém a categoria exata, deve retornar restaurante dessa categoria."""
        result = get_recommendation("quero pizza hoje")
        assert "Pizzaria Saborosa" in result

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_category_match_is_case_insensitive(self, _mock):
        result = get_recommendation("PIZZA")
        assert "Pizzaria Saborosa" in result

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_includes_rating(self, _mock):
        result = get_recommendation("")
        assert "⭐" in result

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_includes_address(self, _mock):
        result = get_recommendation("")
        addresses = {r["address"] for r in MOCK_RESTAURANTS}
        assert any(addr in result for addr in addresses)

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_includes_phone(self, _mock):
        result = get_recommendation("")
        phones = {r["phone"] for r in MOCK_RESTAURANTS}
        assert any(phone in result for phone in phones)

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_fallback_when_no_category_match(self, _mock):
        """Mensagem sem categoria conhecida deve retornar recomendação aleatória válida."""
        random.seed(0)
        result = get_recommendation("quero comer alguma coisa diferente")
        names = {r["name"] for r in MOCK_RESTAURANTS}
        assert any(name in result for name in names)

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_empty_message_returns_random_recommendation(self, _mock):
        result = get_recommendation()  # default = ""
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_deterministic_with_seed_and_single_match(self, _mock):
        """Com apenas um restaurante na categoria, o resultado é sempre o mesmo."""
        result1 = get_recommendation("pizza")
        result2 = get_recommendation("pizza")
        assert result1 == result2  # só existe 1 pizzaria no mock