# 🤖 GenAI Agent Food

API simulada de um agente para restaurante, que envolve machine learning e aceleração de processos em demandas.

---

# Objetivo
Demonstrar um sistema que aplica conceitos de **LLMs**, **MLOps** e **engenharia de software** para criar um agente que:
- Entende intenções do usuário.
- Responde dúvidas sobre pedidos.
- Recomenda restaurantes com base em preferências.
- Opera via API REST com FastAPI.

---

# Arquitetura
![Arquitetura](./docs/architecture-diagram.png)

**Camadas:**
- `API (FastAPI)` – interface de interação.
- `NLP Service` – processamento de linguagem (mock ou modelo real Hugging Face).
- `Recommender` – motor simples de recomendação.
- `MLOps Layer` – scripts para treino e avaliação (simulados).

---

# Endpoints
| Método | Rota | Descrição |
|--------|------|------------|
| GET | `/` | Status da API |
| POST | `/chat` | Envia mensagem e recebe resposta do agente |
| GET | `/restaurants` | Lista restaurantes fictícios |
| GET | `/orders` | Simula status de pedidos |

---

# Execução
## Local
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
