"""
Testes de integração para as rotas da API.

Estratégia:
- Restaurantes: mockamos _load_restaurants e _save_restaurants para não tocar o JSON real.
- Orders: cada teste recebe a lista orders_db limpa via fixture.
- Chat: mockamos process_user_message para isolar a rota do serviço NLP.
"""

import json
import pytest
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures e helpers
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
]


@pytest.fixture(autouse=True)
def clear_orders_db():
    """Limpa o banco de pedidos em memória antes de cada teste."""
    from api.routes import orders as orders_module
    orders_module.orders_db.clear()
    yield
    orders_module.orders_db.clear()


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRoot:
    def test_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_json_with_message_key(self):
        response = client.get("/")
        body = response.json()
        assert "message" in body
        assert isinstance(body["message"], str)


# ---------------------------------------------------------------------------
# GET /restaurants
# ---------------------------------------------------------------------------

class TestListRestaurants:
    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_returns_200(self, _mock):
        response = client.get("/restaurants/")
        assert response.status_code == 200

    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_returns_list_with_correct_length(self, _mock):
        response = client.get("/restaurants/")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_restaurant_has_required_fields(self, _mock):
        response = client.get("/restaurants/")
        restaurant = response.json()[0]
        for field in ("id", "name", "category", "rating", "address", "phone"):
            assert field in restaurant, f"Campo '{field}' ausente"

    @patch("api.routes.restaurants._load_restaurants", return_value=[])
    def test_empty_list_when_no_restaurants(self, _mock):
        response = client.get("/restaurants/")
        assert response.json() == []


# ---------------------------------------------------------------------------
# GET /restaurants/{id}
# ---------------------------------------------------------------------------

class TestGetRestaurant:
    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_returns_correct_restaurant(self, _mock):
        response = client.get("/restaurants/1")
        assert response.status_code == 200
        assert response.json()["name"] == "Pizzaria Saborosa"

    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS)
    def test_returns_404_for_unknown_id(self, _mock):
        response = client.get("/restaurants/999")
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /restaurants
# ---------------------------------------------------------------------------

class TestAddRestaurant:
    NEW_RESTAURANT = {
        "name": "Burger King",
        "category": "Hambúrguer",
        "rating": 4.2,
        "address": "Av. Principal, 1",
        "phone": "(86) 99999-9999",
    }

    @patch("api.routes.restaurants._save_restaurants")
    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS.copy())
    def test_returns_201_on_creation(self, _load, _save):
        response = client.post("/restaurants/", json=self.NEW_RESTAURANT)
        assert response.status_code == 201

    @patch("api.routes.restaurants._save_restaurants")
    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS.copy())
    def test_created_restaurant_has_auto_incremented_id(self, _load, _save):
        response = client.post("/restaurants/", json=self.NEW_RESTAURANT)
        # MOCK_RESTAURANTS tem ids 1 e 2, então o próximo deve ser 3
        assert response.json()["id"] == 3

    @patch("api.routes.restaurants._save_restaurants")
    @patch("api.routes.restaurants._load_restaurants", return_value=MOCK_RESTAURANTS.copy())
    def test_created_restaurant_fields_match_payload(self, _load, _save):
        response = client.post("/restaurants/", json=self.NEW_RESTAURANT)
        body = response.json()
        assert body["name"] == self.NEW_RESTAURANT["name"]
        assert body["category"] == self.NEW_RESTAURANT["category"]

    def test_returns_422_when_rating_above_5(self):
        invalid = {**self.NEW_RESTAURANT, "rating": 6.0}
        response = client.post("/restaurants/", json=invalid)
        assert response.status_code == 422

    def test_returns_422_when_rating_negative(self):
        invalid = {**self.NEW_RESTAURANT, "rating": -1.0}
        response = client.post("/restaurants/", json=invalid)
        assert response.status_code == 422

    def test_returns_422_when_missing_required_field(self):
        incomplete = {"name": "Sem categoria"}
        response = client.post("/restaurants/", json=incomplete)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /orders
# ---------------------------------------------------------------------------

VALID_ORDER = {
    "customer_name": "João Silva",
    "restaurant_id": 1,
    "item": "Pizza Margherita",
    "quantity": 2,
}


class TestCreateOrder:
    def test_returns_201_on_creation(self):
        response = client.post("/orders/", json=VALID_ORDER)
        assert response.status_code == 201

    def test_created_order_has_id(self):
        response = client.post("/orders/", json=VALID_ORDER)
        assert response.json()["id"] == 1

    def test_ids_are_sequential(self):
        client.post("/orders/", json=VALID_ORDER)
        response = client.post("/orders/", json=VALID_ORDER)
        assert response.json()["id"] == 2

    def test_returns_422_when_quantity_is_zero(self):
        response = client.post("/orders/", json={**VALID_ORDER, "quantity": 0})
        assert response.status_code == 422

    def test_returns_422_when_quantity_is_negative(self):
        response = client.post("/orders/", json={**VALID_ORDER, "quantity": -3})
        assert response.status_code == 422

    def test_returns_422_when_missing_customer_name(self):
        incomplete = {k: v for k, v in VALID_ORDER.items() if k != "customer_name"}
        response = client.post("/orders/", json=incomplete)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /orders
# ---------------------------------------------------------------------------

class TestListOrders:
    def test_empty_list_initially(self):
        response = client.get("/orders/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_created_orders(self):
        client.post("/orders/", json=VALID_ORDER)
        client.post("/orders/", json=VALID_ORDER)
        response = client.get("/orders/")
        assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# GET /orders/{id}
# ---------------------------------------------------------------------------

class TestGetOrder:
    def test_returns_correct_order(self):
        client.post("/orders/", json=VALID_ORDER)
        response = client.get("/orders/1")
        assert response.status_code == 200
        assert response.json()["customer_name"] == "João Silva"

    def test_returns_404_for_unknown_order(self):
        response = client.get("/orders/999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /orders/{id}
# ---------------------------------------------------------------------------

class TestDeleteOrder:
    def test_deletes_existing_order(self):
        client.post("/orders/", json=VALID_ORDER)
        response = client.delete("/orders/1")
        assert response.status_code == 200
        assert "removido" in response.json()["message"].lower()

    def test_order_no_longer_exists_after_delete(self):
        client.post("/orders/", json=VALID_ORDER)
        client.delete("/orders/1")
        response = client.get("/orders/1")
        assert response.status_code == 404

    def test_returns_404_when_deleting_nonexistent_order(self):
        response = client.delete("/orders/999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /chat/message
# ---------------------------------------------------------------------------

class TestChatEndpoint:
    def test_returns_200(self):
        response = client.post("/chat/message", json={"message": "oi"})
        assert response.status_code == 200

    def test_response_contains_user_message(self):
        response = client.post("/chat/message", json={"message": "olá"})
        body = response.json()
        assert body["user_message"] == "olá"

    def test_response_contains_agent_response(self):
        response = client.post("/chat/message", json={"message": "olá"})
        body = response.json()
        assert "agent_response" in body
        assert isinstance(body["agent_response"], str)
        assert len(body["agent_response"]) > 0

    def test_returns_422_when_message_missing(self):
        response = client.post("/chat/message", json={})
        assert response.status_code == 422

    @patch("api.routes.chat.process_user_message", return_value="Resposta mockada")
    def test_agent_response_uses_nlp_service(self, mock_nlp):
        response = client.post("/chat/message", json={"message": "qualquer coisa"})
        assert response.json()["agent_response"] == "Resposta mockada"
        mock_nlp.assert_called_once_with("qualquer coisa")