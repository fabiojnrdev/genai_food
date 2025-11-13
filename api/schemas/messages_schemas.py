from pydantic import BaseModel

class MessageBase(BaseModel):
    message: str

class ChatResponse(MessageBase):
    agent_response: str
    user_message: str