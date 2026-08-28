from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


AIContextType = Literal["dashboard", "customer", "opportunity", "quotation"]
AICapability = Literal["sales_copilot", "report_analyst", "quotation_writer"]


class AIChatRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)
    conversation_id: Optional[str] = None
    capability: AICapability = "sales_copilot"
    context_type: AIContextType = "dashboard"
    context_id: Optional[str] = None


class AIMessage(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    capability: AICapability
    context_type: AIContextType
    context_id: Optional[str] = None
    created_at: datetime


class AIConversationDetail(BaseModel):
    id: str
    title: str
    context_type: AIContextType
    context_id: Optional[str] = None
    messages: list[AIMessage]
    created_at: datetime
    updated_at: datetime


class AIContextOption(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class AISaveRequest(BaseModel):
    conversation_id: str
    message_id: str
    target_type: AIContextType
    target_id: Optional[str] = None
    title: str = Field(default="Catatan AI", min_length=2, max_length=120)


class AISavedNote(BaseModel):
    id: str
    target_type: AIContextType
    target_id: Optional[str] = None
    title: str
    content: str
    created_by: str
    created_at: datetime