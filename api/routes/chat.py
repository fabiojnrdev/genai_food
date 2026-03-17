from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.services.auth_service import get_current_user
from api.services.nlp_service import process_user_message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    user_message: str
    agent_response: str


@router.post("/message", response_model=ChatResponse)
def chat(request: ChatRequest, _=Depends(get_current_user)):
    response = process_user_message(request.message)
    return ChatResponse(user_message=request.message, agent_response=response)