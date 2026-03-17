"""
Testes unitários para os serviços de modelo/NLP.

Estratégia:
- _classify_intent_hf é sempre mockada — os testes não fazem chamadas reais à API.
  Isso garante que a suíte rode offline e sem consumir cota da HuggingFace.
- _detect_intent_keywords é testada diretamente como fallback isolado.
- TestHuggingFaceClassifier testa a lógica de score, timeout e cold start.
- recommender: mockamos _load_restaurants para controlar os dados.
"""

import random
import pytest
import requests
from unittest.mock import patch, MagicMock

from api.services.nlp_service import (
    process_user_message,
    _detect_intent,
    _detect_intent_keywords,
    _classify_intent_hf,
)
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
# _detect_intent_keywords (fallback isolado)
# ---------------------------------------------------------------------------

class TestDetectIntentKeywords:
    """Testa o fallback keyword-based diretamente, sem envolver a API."""

    @pytest.mark.parametrize("message,expected", [
        ("cadê meu pedido?",            "order_status"),
        ("quero rastrear minha entrega","order_status"),
        ("qual o status do pedido",     "order_status"),
        ("me recomenda um restaurante", "recommendation"),
        ("onde posso comer hoje?",      "recommendation"),
        ("estou com fome",              "recommendation"),
        ("oi tudo bem",                 "greeting"),
        ("bom dia!",                    "greeting"),
        ("boa noite",                   "greeting"),
        ("preciso de ajuda",            "help"),
        ("como funciona o app?",        "help"),
        ("xkcd 1234 ???",               "unknown"),
        ("",                            "unknown"),
    ])
    def test_keyword_detection(self, message, expected):
        assert _detect_intent_keywords(message) == expected

    def test_is_case_insensitive(self):
        assert _detect_intent_keywords("OI TUDO BEM") == "greeting"
        assert _detect_intent_keywords("PEDIDO") == "order_status"


# ---------------------------------------------------------------------------
# _classify_intent_hf — testa lógica sem chamar API real
# ---------------------------------------------------------------------------

class TestHuggingFaceClassifier:

    @patch("api.services.nlp_service.settings")
    def test_returns_none_when_api_key_empty(self, mock_settings):
        mock_settings.hf_api_key = ""
        result = _classify_intent_hf("oi")
        assert result is None

    @patch("api.services.nlp_service.requests.post")
    @patch("api.services.nlp_service.settings")
    def test_returns_intent_on_high_score(self, mock_settings, mock_post):
        mock_settings.hf_api_key = "hf_fake"
        mock_settings.hf_api_url = "https://fake-url"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "labels": ["saudação", "recomendar restaurante"],
            "scores": [0.95, 0.03],
        }
        mock_post.return_value = mock_response
        result = _classify_intent_hf("oi tudo bem")
        assert result == "greeting"

    @patch("api.services.nlp_service.requests.post")
    @patch("api.services.nlp_service.settings")
    def test_returns_none_on_low_score(self, mock_settings, mock_post):
        """Score abaixo de 0.4 deve acionar o fallback."""
        mock_settings.hf_api_key = "hf_fake"
        mock_settings.hf_api_url = "https://fake-url"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "labels": ["saudação", "recomendar restaurante"],
            "scores": [0.30, 0.25],
        }
        mock_post.return_value = mock_response
        result = _classify_intent_hf("texto ambíguo")
        assert result is None

    @patch("api.services.nlp_service.requests.post")
    @patch("api.services.nlp_service.settings")
    def test_returns_none_on_503_cold_start(self, mock_settings, mock_post):
        """503 = modelo carregando no HuggingFace — deve usar fallback."""
        mock_settings.hf_api_key = "hf_fake"
        mock_settings.hf_api_url = "https://fake-url"
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_post.return_value = mock_response
        result = _classify_intent_hf("qualquer coisa")
        assert result is None

    @patch("api.services.nlp_service.requests.post", side_effect=requests.exceptions.Timeout)
    @patch("api.services.nlp_service.settings")
    def test_returns_none_on_timeout(self, mock_settings, _mock_post):
        mock_settings.hf_api_key = "hf_fake"
        mock_settings.hf_api_url = "https://fake-url"
        result = _classify_intent_hf("qualquer coisa")
        assert result is None

    @patch("api.services.nlp_service.requests.post", side_effect=Exception("erro inesperado"))
    @patch("api.services.nlp_service.settings")
    def test_returns_none_on_unexpected_error(self, mock_settings, _mock_post):
        mock_settings.hf_api_key = "hf_fake"
        mock_settings.hf_api_url = "https://fake-url"
        result = _classify_intent_hf("qualquer coisa")
        assert result is None


# ---------------------------------------------------------------------------
# _detect_intent — integração HF + fallback
# ---------------------------------------------------------------------------

class TestDetectIntent:

    @patch("api.services.nlp_service._classify_intent_hf", return_value="greeting")
    def test_uses_hf_result_when_available(self, _mock):
        assert _detect_intent("oi") == "greeting"

    @patch("api.services.nlp_service._classify_intent_hf", return_value=None)
    def test_falls_back_to_keywords_when_hf_returns_none(self, _mock):
        assert _detect_intent("cadê meu pedido?") == "order_status"

    @patch("api.services.nlp_service._classify_intent_hf", return_value=None)
    def test_returns_unknown_when_both_fail(self, _mock):
        assert _detect_intent("xkcd 9999 ???") == "unknown"


# ---------------------------------------------------------------------------
# process_user_message
# ---------------------------------------------------------------------------

class TestProcessUserMessage:

    def test_empty_message_returns_fallback(self):
        result = process_user_message("")
        assert "não recebi" in result.lower()

    def test_whitespace_only_returns_fallback(self):
        result = process_user_message("   ")
        assert "não recebi" in result.lower()

    @patch("api.services.nlp_service._classify_intent_hf", return_value="greeting")
    def test_greeting_returns_welcome_message(self, _mock):
        result = process_user_message("oi")
        assert "bem-vindo" in result.lower()

    @patch("api.services.nlp_service._classify_intent_hf", return_value="help")
    def test_help_returns_capabilities_list(self, _mock):
        result = process_user_message("preciso de ajuda")
        assert "recomendar" in result.lower()
        assert "pedido" in result.lower()

    @patch("api.services.nlp_service._classify_intent_hf", return_value="order_status")
    def test_order_status_returns_status_message(self, _mock):
        result = process_user_message("onde está meu pedido?")
        assert "caminho" in result.lower() or "preparado" in result.lower()

    @patch("api.services.nlp_service._classify_intent_hf", return_value=None)
    def test_unknown_intent_returns_clarification_request(self, _mock):
        result = process_user_message("xkcd 9999 ???")
        assert "não entendi" in result.lower()

    @patch("api.services.nlp_service._classify_intent_hf", return_value="recommendation")
    @patch("api.services.nlp_service.get_recommendation", return_value="Recomendo a Pizzaria X")
    def test_recommendation_intent_calls_recommender(self, mock_rec, _mock_hf):
        result = process_user_message("me recomenda algo")
        mock_rec.assert_called_once_with("me recomenda algo")
        assert result == "Recomendo a Pizzaria X"

    @patch("api.services.nlp_service._classify_intent_hf", return_value="recommendation")
    @patch("api.services.nlp_service.get_recommendation", return_value="Mock")
    def test_recommendation_passes_original_message_to_recommender(self, mock_rec, _mock_hf):
        process_user_message("Quero comer Pizza")
        mock_rec.assert_called_once_with("Quero comer Pizza")


# ---------------------------------------------------------------------------
# get_recommendation
# ---------------------------------------------------------------------------

_FIXED_RESTAURANT = MOCK_RESTAURANTS[0]  # Pizzaria Saborosa — usado como resultado fixo


class TestGetRecommendation:
    @patch("api.services.recommender.random.choice", return_value=_FIXED_RESTAURANT)
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_returns_non_empty_string(self, _load, _choice):
        result = get_recommendation("quero comer algo")
        assert isinstance(result, str) and len(result) > 0

    @patch("api.services.recommender.random.choice", return_value=_FIXED_RESTAURANT)
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_contains_restaurant_name(self, _load, _choice):
        assert _FIXED_RESTAURANT["name"] in get_recommendation("")

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_category_match_returns_matching_restaurant(self, _mock):
        assert "Pizzaria Saborosa" in get_recommendation("quero pizza hoje")

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_category_match_is_case_insensitive(self, _mock):
        assert "Pizzaria Saborosa" in get_recommendation("PIZZA")

    @patch("api.services.recommender.random.choice", return_value=_FIXED_RESTAURANT)
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_includes_rating(self, _load, _choice):
        assert "⭐" in get_recommendation("")

    @patch("api.services.recommender.random.choice", return_value=_FIXED_RESTAURANT)
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_includes_address(self, _load, _choice):
        assert _FIXED_RESTAURANT["address"] in get_recommendation("")

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_recommendation_includes_phone(self, _load):
        """Verifica que o telefone aparece para cada restaurante possível."""
        for restaurant in MOCK_RESTAURANTS:
            with patch("api.services.recommender.random.choice", return_value=restaurant):
                assert restaurant["phone"] in get_recommendation("")

    @patch("api.services.recommender.random.choice", return_value=_FIXED_RESTAURANT)
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_fallback_when_no_category_match(self, _load, _choice):
        """Mensagem sem categoria conhecida deve retornar recomendação aleatória válida."""
        result = get_recommendation("quero comer alguma coisa diferente")
        assert _FIXED_RESTAURANT["name"] in result

    @patch("api.services.recommender.random.choice", return_value=_FIXED_RESTAURANT)
    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_empty_message_returns_random_recommendation(self, _load, _choice):
        result = get_recommendation()
        assert isinstance(result, str) and len(result) > 0

    @patch("api.services.recommender._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_deterministic_with_seed_and_single_match(self, _mock):
        """Com único match de categoria o resultado é sempre o mesmo."""
        assert get_recommendation("pizza") == get_recommendation("pizza")