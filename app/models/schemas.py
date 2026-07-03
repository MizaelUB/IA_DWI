from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    model: str = "llama3.2:3b"
    concept_model: str = "llama3.2:3b"
    limit_chunks: int = 5
    history: List[Message] = []
    autonomous_search: bool = False
    veterinary_id: int | None = None
    conversation_id: str | None = None
    user_id: int | None = None
    is_follow_up: bool = False
