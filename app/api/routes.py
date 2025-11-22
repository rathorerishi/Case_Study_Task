
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, status
from typing import Optional
from app.schemas.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
    MessageCreate,
    MessageResponse,
    AddMessageResponse,
    DocumentUploadResponse,
    HealthResponse
)
from app.services.conversation_service import conversation_service
from app.services.rag_service import rag_service
from app.database.mongodb import MongoDB
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    
    try:
        # Check database connection
        db = MongoDB.get_database()
        await db.command('ping')
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": db_status,
        "llm_service": "healthy"
    }


@router.post(
    "/conversations",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    tags=["Conversations"]
)
async def create_conversation(data: ConversationCreate):
    
    try:
        conversation, user_msg, assistant_msg = await conversation_service.create_conversation(
            user_id=data.user_id,
            first_message=data.first_message,
            mode=data.mode
        )
        
        return {
            "conversation_id": conversation["_id"],
            "conversation": conversation,
            "user_message": user_msg,
            "assistant_message": assistant_msg
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    tags=["Conversations"]
)
async def list_conversations(
    user_id: str = Query(..., description="User ID to list conversations for"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    

    try:
        result = await conversation_service.list_conversations(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    tags=["Conversations"]
)
async def get_conversation(conversation_id: str):
    
    try:
        conversation = await conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        messages = await conversation_service.get_conversation_messages(conversation_id)
        
        return {
            "conversation": conversation,
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AddMessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Messages"]
)
async def add_message(conversation_id: str, data: MessageCreate):
    
    try:
        user_msg, assistant_msg = await conversation_service.add_message(
            conversation_id=conversation_id,
            content=data.content
        )
        
        return {
            "user_message": user_msg,
            "assistant_message": assistant_msg
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Conversations"]
)
async def delete_conversation(conversation_id: str):
    
    try:
        success = await conversation_service.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.post(
    "/conversations/{conversation_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"]
)
async def upload_document(
    conversation_id: str,
    file: UploadFile = File(...)
):
   
    try:
        # Validate conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX, TXT"
            )
        
        # Validate file size (10MB max)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
        
        # Process document
        document = await rag_service.process_document(
            conversation_id=conversation_id,
            filename=file.filename,
            file_content=file_content,
            content_type=file.content_type
        )
        
        return document
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get(
    "/conversations/{conversation_id}/documents",
    response_model=list,
    tags=["Documents"]
)
async def list_documents(conversation_id: str):
    
    try:
        documents = await rag_service.get_conversation_documents(conversation_id)
        return documents
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )