from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConversationMode(str, Enum):
    """Conversation modes supported by the system."""
    OPEN_CHAT = "open_chat"
    GROUNDED_RAG = "grounded_rag"


class MessageRole(str, Enum):
    """Message roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"



# Conversation Schemas
class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    user_id: str
    first_message: str
    mode: ConversationMode = ConversationMode.OPEN_CHAT

class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str = Field(alias="_id")
    user_id: str
    title: str
    mode: ConversationMode
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
    class Config:
        populate_by_name = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    limit: int
    pages: int


# Message Schemas
class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str = Field(alias="_id")
    conversation_id: str
    role: MessageRole
    content: str
    sequence_number: int
    tokens_used: int
    created_at: datetime
    metadata: Dict[str, Any] = {}
    
    class Config:
        populate_by_name = True


class ConversationDetailResponse(BaseModel):
    """Schema for conversation with full message history."""
    conversation: ConversationResponse
    messages: List[MessageResponse]


class AddMessageResponse(BaseModel):
    """Schema for response when adding a message."""
    user_message: MessageResponse
    assistant_message: MessageResponse


# Document Schemas for RAG
class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    id: str = Field(alias="_id")
    conversation_id: str
    filename: str
    file_size: int
    content_type: str
    chunks_count: int
    created_at: datetime
    
    class Config:
        populate_by_name = True


# Health Check Schema
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    database: str
    llm_service: str