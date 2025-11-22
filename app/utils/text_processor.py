import re
from typing import List, Dict
from PyPDF2 import PdfReader
import docx
import logging

logger = logging.getLogger(__name__)
class TextProcessor:
    #Text processing utilities for RAG.
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        
        # Extract text from PDF file.
        
        try:
            import io
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        
        # Extract text from DOCX file.
        
        try:
            import io
            docx_file = io.BytesIO(file_content)
            doc = docx.Document(docx_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = 600, 
        overlap: int = 100
    ) -> List[Dict[str, any]]:
        
        # Split text into overlapping chunks.
        
        # Split text into words
        words = text.split()
        
        if len(words) <= chunk_size:
            return [{
                "chunk_id": "chunk_0",
                "text": text,
                "start_word": 0,
                "end_word": len(words),
                "word_count": len(words)
            }]
        
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "chunk_id": f"chunk_{chunk_index}",
                "text": chunk_text,
                "start_word": start,
                "end_word": end,
                "word_count": len(chunk_words)
            })
            
            chunk_index += 1
            start = end - overlap if end < len(words) else end
        
        return chunks
    
    @staticmethod
    def calculate_relevance_score(query: str, chunk_text: str) -> float:
        
        # Calculate simple relevance score between query and chunk. Uses keyword matching and word overlap.
        
        query_words = set(re.sub(r'[^\w\s]', '', query.lower()).split())
        chunk_words = set(re.sub(r'[^\w\s]', '', chunk_text.lower()).split())
        
        if not query_words or not chunk_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = query_words.intersection(chunk_words)
        union = query_words.union(chunk_words)
        
        return len(intersection) / len(union) if union else 0.0


# Global text processor instance
text_processor = TextProcessor()