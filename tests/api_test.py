"""
Testes de integração para as rotas da API.

Estratégia:
- Restaurantes: mockamos _load_restaurants e _save_restaurants para não tocar o JSON real.
- Orders: banco SQLite em memória (:memory:) injetado via override de dependência do FastAPI.
  Isso garante isolamento total — cada sessão de testes começa com banco limpo.
- Chat: mockamos process_user_message para isolar a rota do serviço NLP.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.database import Base, get_db
from api.config import get_settings, Settings
from api.models import order_model, user_model  # noqa: F401 — registra models no Base.metadata

# ---------------------------------------------------------------------------
# Banco em memória para testes de orders
#
# SQLite :memory: isola cada conexão — se create_all e a sessão usarem
# conexões diferentes, a tabela não existe para a sessão.
# Solução: criar UMA conexão única e forçar todas as operações nela.
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Conexão única reutilizada por toda a sessão de testes
_connection = test_engine.connect()

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_connection,   # sessão vinculada à mesma conexão do create_all
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Bypass de autenticação para os testes existentes
from api.services.auth_service import get_current_user
app.dependency_overrides[get_current_user] = lambda: "test-user"

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
def setup_database():
    """
    Cria tabelas na conexão compartilhada antes de cada teste.
    Usa transação aninhada (SAVEPOINT) para rollback limpo ao final —
    sem precisar recriar o schema a cada teste.
    """
    Base.metadata.create_all(bind=_connection)
    transaction = _connection.begin_nested()   # SAVEPOINT
    yield
    transaction.rollback()                     # desfaz dados do teste


# ---------------------------------------------------------------------------
# Settings / config
# ---------------------------------------------------------------------------

class TestSettings:
    def test_default_env_is_dev(self):
        get_settings.cache_clear()
        s = Settings()
        assert s.env == "dev"

    def test_is_dev_property(self):
        s = Settings(env="dev")
        assert s.is_dev is True

    def test_is_not_dev_in_prod(self):
        s = Settings(env="prod")
        assert s.is_dev is False

    def test_hf_api_url_contains_model_name(self):
        s = Settings(hf_model="some-org/some-model")
        assert "some-org/some-model" in s.hf_api_url

    def test_hf_api_key_not_exposed_in_repr(self):
        s = Settings(hf_api_key="hf_secret123")
        assert "hf_secret123" not in repr(s)

    def test_restaurants_data_path_is_path_instance(self):
        from pathlib import Path
        s = Settings()
        assert isinstance(s.restaurants_data_path, Path)


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

# ---------------------------------------------------------------------------
# Auth — /auth/register e /auth/token
# ---------------------------------------------------------------------------

class TestAuthRegister:
    def test_register_returns_201(self):
        # Remove override de auth para testar as rotas de auth diretamente
        app.dependency_overrides.pop(get_current_user, None)
        response = client.post("/auth/register", json={"username": "fabio", "password": "senha123"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 201

    def test_register_returns_user_fields(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.post("/auth/register", json={"username": "fabio2", "password": "senha123"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        body = response.json()
        assert body["username"] == "fabio2"
        assert "password" not in body
        assert body["is_active"] is True

    def test_register_duplicate_returns_409(self):
        app.dependency_overrides.pop(get_current_user, None)
        client.post("/auth/register", json={"username": "duplicado", "password": "senha123"})
        response = client.post("/auth/register", json={"username": "duplicado", "password": "outrasenha"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 409


class TestAuthToken:
    def test_login_returns_token(self):
        app.dependency_overrides.pop(get_current_user, None)
        client.post("/auth/register", json={"username": "tokenuser", "password": "senha123"})
        response = client.post("/auth/token", json={"username": "tokenuser", "password": "senha123"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self):
        app.dependency_overrides.pop(get_current_user, None)
        client.post("/auth/register", json={"username": "wrongpass", "password": "certa"})
        response = client.post("/auth/token", json={"username": "wrongpass", "password": "errada"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 401

    def test_login_unknown_user_returns_401(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.post("/auth/token", json={"username": "naoexiste", "password": "qualquer"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 401


class TestAuthProtection:
    """Garante que as rotas retornam 401 sem credenciais."""

    def test_get_restaurants_without_auth_returns_401(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.get("/restaurants/")
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 401

    def test_get_orders_without_auth_returns_401(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.get("/orders/")
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 401

    def test_api_key_header_grants_access(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.get("/restaurants/", headers={"X-API-Key": "chave-dev-1"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        # 200 ou 500 de IO são aceitáveis — o que não pode é 401
        assert response.status_code != 401

    def test_invalid_api_key_returns_401(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.get("/orders/", headers={"X-API-Key": "chave-invalida"})
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 401

# ---------------------------------------------------------------------------
# Middleware e handlers de erro
# ---------------------------------------------------------------------------

class TestErrorHandlers:
    def test_404_returns_json_error_format(self):
        response = client.get("/rota-que-nao-existe")
        assert response.status_code == 404
        body = response.json()
        assert "error" in body
        assert "status" in body["error"]
        assert "message" in body["error"]

    def test_422_returns_json_error_format_with_details(self):
        # POST em /orders sem body obrigatório → 422
        response = client.post("/orders/", json={})
        assert response.status_code == 422
        body = response.json()
        assert "error" in body
        assert "details" in body["error"]
        assert isinstance(body["error"]["details"], list)

    def test_401_returns_json_error_format(self):
        app.dependency_overrides.pop(get_current_user, None)
        response = client.get("/orders/")
        app.dependency_overrides[get_current_user] = lambda: "test-user"
        assert response.status_code == 401
        body = response.json()
        assert "error" in body

    def test_request_logging_does_not_break_response(self):
        """O middleware de log não deve alterar o conteúdo da resposta."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] is not None