from fastapi import APIRouter
from api.schemas.messages_schemas import ChatRequest, ChatResponse
from api.services.nlp_service import process_user_message

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    response = process_message(request.message)
    return {"user_message": request.message, "agent_response": response}
