# Token counting utilities for managing LLM context.
# Provides functions to count tokens and manage conversation history.

import tiktoken
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)
class TokenCounter:
    #Token counter for LLM context management.
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        
        # Initialize token counter with specific encoding.
        
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
    
    def count_tokens(self, text: str) -> int:
        
        # Count tokens in a text string.
        
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        
        # Count total tokens in a list of messages.
        
        total_tokens = 0
        for message in messages:
            # Each message has overhead: role + content + formatting
            total_tokens += 4  # Message overhead
            total_tokens += self.count_tokens(message.get("role", ""))
            total_tokens += self.count_tokens(message.get("content", ""))
        total_tokens += 2  # Conversation overhead
        return total_tokens
    
    def truncate_messages(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int,
        keep_system: bool = True
    ) -> List[Dict[str, str]]:
        
        # Truncate messages to fit within token limit.
        
        if not messages:
            return messages
        
        # Separate system messages if keeping them
        system_messages = []
        other_messages = []
        
        if keep_system:
            for msg in messages:
                if msg.get("role") == "system":
                    system_messages.append(msg)
                else:
                    other_messages.append(msg)
        else:
            other_messages = messages
        
        # Count tokens for system messages
        system_tokens = self.count_message_tokens(system_messages)
        remaining_tokens = max_tokens - system_tokens
        
        if remaining_tokens <= 0:
            logger.warning("System messages exceed token limit")
            return system_messages[:1]  # Keep only first system message
        
        # Add messages from most recent, working backwards
        result_messages = []
        current_tokens = 0
        
        for message in reversed(other_messages):
            message_tokens = self.count_message_tokens([message])
            if current_tokens + message_tokens <= remaining_tokens:
                result_messages.insert(0, message)
                current_tokens += message_tokens
            else:
                break
        
        return system_messages + result_messages


# Global token counter instance
token_counter = TokenCounter()