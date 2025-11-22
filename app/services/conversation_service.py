from typing import List, Dict, Optional, Tuple
from bson import ObjectId
from datetime import datetime
from app.database.mongodb import MongoDB, Collections
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.schemas.schemas import ConversationMode, MessageRole
import logging
import math

logger = logging.getLogger(__name__)


class ConversationService:
    # Service for conversation management
    
    async def create_conversation(
        self,
        user_id: str,
        first_message: str,
        mode: ConversationMode = ConversationMode.OPEN_CHAT
    ) -> Tuple[Dict, Dict, Dict]:
        
        try:
            db = MongoDB.get_database()
            
            # Create conversation
            conversation = {
                "user_id": ObjectId(user_id),
                "title": first_message[:50] + "..." if len(first_message) > 50 else first_message,
                "mode": mode.value,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "total_messages": 0,
                    "total_tokens": 0
                }
            }
            
            result = await db[Collections.CONVERSATIONS].insert_one(conversation)
            conversation_id = str(result.inserted_id)
            
            # Convert ObjectIds to strings for response
            conversation["_id"] = conversation_id
            conversation["user_id"] = user_id
            
            # Create user message
            user_message = await self._create_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=first_message,
                sequence_number=1
            )
            
            # Generate AI response
            assistant_message = await self._generate_and_store_response(
                conversation_id=conversation_id,
                user_message_content=first_message,
                conversation_history=[],
                sequence_number=2,
                mode=mode
            )
            
            # Update conversation metadata
            await self._update_conversation_stats(
                conversation_id,
                user_message["tokens_used"] + assistant_message["tokens_used"]
            )
            
            logger.info(f"Conversation created: {conversation_id}")
            
            return conversation, user_message, assistant_message
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def add_message(
        self,
        conversation_id: str,
        content: str
    ) -> Tuple[Dict, Dict]:
        # Add user message to conversation and get AI response.
        try:
            # Get conversation
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Get conversation history
            messages = await self.get_conversation_messages(conversation_id)
            
            # Create user message
            sequence_number = len(messages) + 1
            user_message = await self._create_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=content,
                sequence_number=sequence_number
            )
            
            # Build conversation history for LLM
            conversation_history = self._build_conversation_history(messages)
            
            # Generate AI response
            assistant_message = await self._generate_and_store_response(
                conversation_id=conversation_id,
                user_message_content=content,
                conversation_history=conversation_history,
                sequence_number=sequence_number + 1,
                mode=ConversationMode(conversation["mode"])
            )
            
            # Update conversation metadata
            await self._update_conversation_stats(
                conversation_id,
                user_message["tokens_used"] + assistant_message["tokens_used"]
            )
            
            logger.info(f"Message added to conversation {conversation_id}")
            
            return user_message, assistant_message
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        # Get conversation by ID.
        try:
            db = MongoDB.get_database()
            conversation = await db[Collections.CONVERSATIONS].find_one({
                "_id": ObjectId(conversation_id)
            })
            
            if conversation:
                conversation["_id"] = str(conversation["_id"])
                conversation["user_id"] = str(conversation["user_id"])
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        # Get all messages for a conversation, ordered by sequence.
        try:
            db = MongoDB.get_database()
            messages = await db[Collections.MESSAGES].find({
                "conversation_id": ObjectId(conversation_id)
            }).sort("sequence_number", 1).to_list(length=None)
            
            # Convert ObjectIds to strings
            for msg in messages:
                msg["_id"] = str(msg["_id"])
                msg["conversation_id"] = str(msg["conversation_id"])
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    async def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Dict:
        # List conversations for a user with pagination.
        try:
            db = MongoDB.get_database()
            skip = (page - 1) * limit
            
            # Get total count
            total = await db[Collections.CONVERSATIONS].count_documents({
                "user_id": ObjectId(user_id)
            })
            
            # Get conversations
            conversations = await db[Collections.CONVERSATIONS].find({
                "user_id": ObjectId(user_id)
            }).sort("updated_at", -1).skip(skip).limit(limit).to_list(length=limit)
            
            # Convert ObjectIds
            for conv in conversations:
                conv["_id"] = str(conv["_id"])
                conv["user_id"] = str(conv["user_id"])
            
            pages = math.ceil(total / limit) if total > 0 else 1
            
            return {
                "conversations": conversations,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }
            
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return {
                "conversations": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        # Delete conversation and all associated messages and documents.
        try:
            db = MongoDB.get_database()
            
            # Delete messages
            await db[Collections.MESSAGES].delete_many({
                "conversation_id": ObjectId(conversation_id)
            })
            
            # Delete documents
            await rag_service.delete_conversation_documents(conversation_id)
            
            # Delete conversation
            result = await db[Collections.CONVERSATIONS].delete_one({
                "_id": ObjectId(conversation_id)
            })
            
            logger.info(f"Conversation {conversation_id} deleted")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
    
    async def _create_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        sequence_number: int,
        tokens_used: int = 0,
        metadata: Dict = None
    ) -> Dict:
        #Create and store a message.
        db = MongoDB.get_database()
        
        # Count tokens if not provided
        if tokens_used == 0:
            tokens_used = llm_service.count_tokens(content)
        
        message = {
            "conversation_id": ObjectId(conversation_id),
            "role": role.value,
            "content": content,
            "sequence_number": sequence_number,
            "tokens_used": tokens_used,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        result = await db[Collections.MESSAGES].insert_one(message)
        
        # Convert ObjectIds to strings for response
        message["_id"] = str(result.inserted_id)
        message["conversation_id"] = conversation_id
        
        return message
    
    async def _generate_and_store_response(
        self,
        conversation_id: str,
        user_message_content: str,
        conversation_history: List[Dict],
        sequence_number: int,
        mode: ConversationMode
    ) -> Dict:
        #Generate AI response and store it.
        # Generate response based on mode
        if mode == ConversationMode.GROUNDED_RAG:
            # Retrieve relevant chunks
            chunks = await rag_service.retrieve_relevant_chunks(
                conversation_id=conversation_id,
                query=user_message_content,
                top_k=3
            )
            
            if chunks:
                # Generate with RAG context
                response = await llm_service.generate_with_rag_context(
                    user_message=user_message_content,
                    conversation_history=conversation_history,
                    retrieved_chunks=chunks
                )
            else:
                # No documents available, fall back to open chat
                logger.warning(f"No documents found for RAG mode in conversation {conversation_id}")
                messages = conversation_history + [{
                    "role": "user",
                    "content": user_message_content
                }]
                response = await llm_service.generate_response(messages)
        else:
            # Open chat mode
            messages = conversation_history + [{
                "role": "user",
                "content": user_message_content
            }]
            response = await llm_service.generate_response(messages)
        
        # Store assistant message
        assistant_message = await self._create_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response["content"],
            sequence_number=sequence_number,
            tokens_used=response["tokens_used"],
            metadata={
                "model": response.get("model"),
                "finish_reason": response.get("finish_reason"),
                "chunks_used": response.get("chunks_used", 0)
            }
        )
        
        return assistant_message
    
    def _build_conversation_history(self, messages: List[Dict]) -> List[Dict[str, str]]:
        #Build conversation history in LLM format.
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]
    
    async def _update_conversation_stats(self, conversation_id: str, tokens_added: int):
        #Update conversation statistics.
        db = MongoDB.get_database()
        await db[Collections.CONVERSATIONS].update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {
                    "metadata.total_messages": 2,  # User + assistant
                    "metadata.total_tokens": tokens_added
                }
            }
        )


# Global conversation service instance
conversation_service = ConversationService()