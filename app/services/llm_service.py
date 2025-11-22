
from groq import Groq
from typing import List, Dict, Optional
from app.config import settings
from app.utils.token_counter import token_counter
import logging
import asyncio

logger = logging.getLogger(__name__)


class LLMService:
    #Service for LLM API interactions.
    
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.max_tokens = settings.max_tokens
        self.max_history = settings.max_conversation_history
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, any]:
        # Generate response from LLM.
        try:
            # Manage context to fit within token limits
            managed_messages = self._manage_context(messages)
            
            # Make async API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=managed_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            )
            
            assistant_message = response.choices[0].message.content
            
            # Calculate tokens used
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            logger.info(f"LLM response generated successfully. Tokens used: {tokens_used}")
            
            return {
                "content": assistant_message,
                "tokens_used": tokens_used,
                "model": self.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Return fallback response
            return {
                "content": "I apologize, but I'm having trouble generating a response right now. Please try again.",
                "tokens_used": 0,
                "model": self.model,
                "error": str(e)
            }
    
    def _manage_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        # Manage conversation context to fit within token limits.
        # First, apply sliding window
        if len(messages) > self.max_history:
            # Keep system message if present
            system_messages = [m for m in messages if m.get("role") == "system"]
            other_messages = [m for m in messages if m.get("role") != "system"]
            
            # Keep last N non-system messages
            windowed_messages = other_messages[-(self.max_history - len(system_messages)):]
            messages = system_messages + windowed_messages
        
        # Then, check token count and truncate if necessary
        total_tokens = token_counter.count_message_tokens(messages)
        
        if total_tokens > self.max_tokens:
            logger.warning(f"Message tokens ({total_tokens}) exceed limit ({self.max_tokens}). Truncating...")
            messages = token_counter.truncate_messages(messages, self.max_tokens)
            logger.info(f"Messages truncated. New token count: {token_counter.count_message_tokens(messages)}")
        
        return messages
    
    async def generate_with_rag_context(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        retrieved_chunks: List[str],
        temperature: float = 0.7
    ) -> Dict[str, any]:
        
        # Generate response with RAG context.
        
        # Build RAG-enhanced prompt
        context = "\n\n".join([f"[Document Excerpt {i+1}]\n{chunk}" for i, chunk in enumerate(retrieved_chunks)])
        
        rag_system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer the user's question based on the provided document excerpts. "
                "If the answer cannot be found in the provided context, say so clearly. "
                "Always cite which document excerpt you're using when answering."
            )
        }
        
        context_message = {
            "role": "system",
            "content": f"Relevant document context:\n\n{context}"
        }
        
        user_query = {
            "role": "user",
            "content": user_message
        }
        
        # Combine messages: system + context + history + current query
        messages = [rag_system_message, context_message] + conversation_history + [user_query]
        
        # Generate response
        response = await self.generate_response(messages, temperature=temperature)
        
        # Add metadata about chunks used
        response["chunks_used"] = len(retrieved_chunks)
        
        return response
    
    def count_tokens(self, text: str) -> int:
        
        # Count tokens in a text string.
        
        return token_counter.count_tokens(text)


# Global LLM service instance
llm_service = LLMService()