from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    session_id: Optional[str] = None  # 없으면 서버에서 새로 만들어줌
    message: str
    email: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
