from typing import List, Dict, Optional
from bson import ObjectId
from app.database.mongodb import MongoDB, Collections
from app.utils.text_processor import text_processor
from app.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGService:
    #Service for RAG functionality.
    
    def __init__(self):
        #Initialize RAG service.
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    async def process_document(
        self,
        conversation_id: str,
        filename: str,
        file_content: bytes,
        content_type: str
    ) -> Dict[str, any]:
        
        # Process uploaded document: extract text, chunk, and store.
        
        try:
            # Extract text based on file type
            if content_type == "application/pdf":
                raw_text = text_processor.extract_text_from_pdf(file_content)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                raw_text = text_processor.extract_text_from_docx(file_content)
            elif content_type == "text/plain":
                raw_text = file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {content_type}")
            
            # Chunk the text
            chunks = text_processor.chunk_text(
                raw_text,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap
            )
            
            # Create document record
            document = {
                "conversation_id": ObjectId(conversation_id),
                "filename": filename,
                "file_size": len(file_content),
                "content_type": content_type,
                "raw_text": raw_text,
                "chunks": chunks,
                "created_at": datetime.utcnow()
            }
            
            # Store in database
            db = MongoDB.get_database()
            result = await db[Collections.DOCUMENTS].insert_one(document)
            
            logger.info(f"Document processed: {filename}, {len(chunks)} chunks created")
            
            return {
                "_id": str(result.inserted_id),
                "conversation_id": conversation_id,
                "filename": filename,
                "file_size": len(file_content),
                "content_type": content_type,
                "chunks_count": len(chunks),
                "created_at": document["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    async def retrieve_relevant_chunks(
        self,
        conversation_id: str,
        query: str,
        top_k: int = 3
    ) -> List[str]:
        
        # Retrieve most relevant chunks for a query.
        
        try:
            # Get all documents for this conversation
            db = MongoDB.get_database()
            documents = await db[Collections.DOCUMENTS].find({
                "conversation_id": ObjectId(conversation_id)
            }).to_list(length=None)
            
            if not documents:
                logger.warning(f"No documents found for conversation {conversation_id}")
                return []
            
            # Collect all chunks with relevance scores
            scored_chunks = []
            
            for doc in documents:
                chunks = doc.get("chunks", [])
                for chunk in chunks:
                    score = text_processor.calculate_relevance_score(query, chunk["text"])
                    scored_chunks.append({
                        "text": chunk["text"],
                        "score": score,
                        "chunk_id": chunk["chunk_id"],
                        "document": doc["filename"]
                    })
            
            # Sort by relevance score
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top K chunks
            top_chunks = scored_chunks[:top_k]
            
            logger.info(f"Retrieved {len(top_chunks)} relevant chunks for query")
            
            return [chunk["text"] for chunk in top_chunks]
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    async def get_conversation_documents(self, conversation_id: str) -> List[Dict[str, any]]:
        
        # Get all documents associated with a conversation.
        
        try:
            db = MongoDB.get_database()
            documents = await db[Collections.DOCUMENTS].find({
                "conversation_id": ObjectId(conversation_id)
            }, {
                "raw_text": 0,  # Exclude raw text for performance
                "chunks": 0     # Exclude chunks for performance
            }).to_list(length=None)
            
            # Convert ObjectIds to strings
            for doc in documents:
                doc["_id"] = str(doc["_id"])
                doc["conversation_id"] = str(doc["conversation_id"])
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    async def delete_conversation_documents(self, conversation_id: str) -> int:
        
        # Delete all documents for a conversation.
        
        try:
            db = MongoDB.get_database()
            result = await db[Collections.DOCUMENTS].delete_many({
                "conversation_id": ObjectId(conversation_id)
            })
            
            logger.info(f"Deleted {result.deleted_count} documents for conversation {conversation_id}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0


# Global RAG service instance
rag_service = RAGService()