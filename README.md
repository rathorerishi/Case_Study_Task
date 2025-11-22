# BOT GPT - Conversational AI Backend

A production-grade conversational AI platform with RAG (Retrieval-Augmented Generation) support, built with FastAPI and MongoDB.

## Features

- **Dual Conversation Modes**
  - Open Chat: General-purpose conversations with LLM
  - Grounded RAG: Document-based conversations with context retrieval

- **Complete REST API**
  - Create and manage conversations
  - Add messages and get AI responses
  - Document upload and processing for RAG
  - Conversation history management
  - Pagination support

- **Smart Context Management**
  - Sliding window for conversation history (last 12 messages)
  - Token counting and optimization (max 7000 tokens)
  - Automatic context truncation

- **RAG Implementation**
  - Document chunking with overlap (600 words, 100-word overlap)
  - Keyword-based relevance scoring 
  - Multi-document support per conversation
  - PDF, DOCX, and TXT file support


## Prerequisites

- Python 3.11+
- MongoDB Atlas
- Groq API Key (free at [console.groq.com](https://console.groq.com))

## Installation

### Local Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd bot-gpt-backend
```

2. **Create virtual environment**
```bash
conda create -p venv python==3.12
conda activate venv/ 
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
```

Edit `.env` and configure:
```env
# MongoDB Configuration (Use MongoDB Atlas)

# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/

MONGODB_DB_NAME=username

# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Context Management
MAX_CONVERSATION_HISTORY=12
MAX_TOKENS=7000
CHUNK_SIZE=600
CHUNK_OVERLAP=100

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
```

5. **Start MongoDB**

**MongoDB Atlas**
- Sign up at [mongodb.com/atlas](https://www.mongodb.com/atlas)
- Create a free cluster
- Get connection string and update `MONGODB_URL` in `.env`

6. **Run the application**
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs

## Manual Testing in Swagger UI

### Step 1: Check Health Status

1. Open http://localhost:8000/docs
2. Find **GET /api/v1/health** endpoint
3. Click **"Try it out"** → **"Execute"**
4. You should see:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "database": "healthy",
  "llm_service": "healthy"
}
```

### Step 2: Create Your First Conversation (Open Chat Mode)

1. Find **POST /api/v1/conversations** endpoint
2. Click **"Try it out"**
3. Replace the request body with:
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "first_message": "Hello! Can you explain what machine learning is?",
  "mode": "open_chat"
}
```
4. Click **"Execute"**
5. **Save the `conversation_id`** from the response - you'll need it!

**Expected Response:**
```json
{
  "conversation_id": "65a1b2c3d4e5f6g7h8i9j0k1",
  "conversation": {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "user_id": "507f1f77bcf86cd799439011",
    "title": "Hello! Can you explain what machine learning is?",
    "mode": "open_chat",
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "metadata": {
      "total_messages": 2,
      "total_tokens": 450
    }
  },
  "user_message": { /* user message details */ },
  "assistant_message": { /* AI response */ }
}
```

### Step 3: Add More Messages to the Conversation

1. Find **POST /api/v1/conversations/{conversation_id}/messages**
2. Click **"Try it out"**
3. Enter your `conversation_id` from Step 2
4. Request body:
```json
{
  "content": "Can you give me some real-world examples?"
}
```
5. Click **"Execute"**

**Expected Response:**
```json
{
  "user_message": {
    "_id": "...",
    "conversation_id": "...",
    "role": "user",
    "content": "Can you give me some real-world examples?",
    "sequence_number": 3,
    "tokens_used": 12,
    "created_at": "...",
    "metadata": {}
  },
  "assistant_message": {
    "_id": "...",
    "conversation_id": "...",
    "role": "assistant",
    "content": "Here are some real-world examples...",
    "sequence_number": 4,
    "tokens_used": 150,
    "created_at": "...",
    "metadata": {
      "model": "llama-3.3-70b-versatile",
      "finish_reason": "stop",
      "chunks_used": 0
    }
  }
}
```

### Step 4: View Conversation History

1. Find **GET /api/v1/conversations/{conversation_id}**
2. Click **"Try it out"**
3. Enter your `conversation_id`
4. Click **"Execute"**

You'll see the complete conversation with all messages in order.

### Step 5: List All Conversations for a User

1. Find **GET /api/v1/conversations**
2. Click **"Try it out"**
3. Enter parameters:
   - `user_id`: `507f1f77bcf86cd799439011`
   - `page`: `1`
   - `limit`: `20`
4. Click **"Execute"**

**Expected Response:**
```json
{
  "conversations": [
    {
      "_id": "...",
      "user_id": "507f1f77bcf86cd799439011",
      "title": "Hello! Can you explain...",
      "mode": "open_chat",
      "created_at": "...",
      "updated_at": "...",
      "metadata": {
        "total_messages": 4,
        "total_tokens": 612
      }
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

### Step 6: Test RAG Mode with Document Upload

#### 6a. Create a RAG Conversation

1. Find **POST /api/v1/conversations**
2. Click **"Try it out"**
3. Request body:
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "first_message": "I want to ask questions about documents I'll upload",
  "mode": "grounded_rag"
}
```
4. Click **"Execute"**
5. **Save the `conversation_id`**

#### 6b. Upload a Document

1. Find **POST /api/v1/conversations/{conversation_id}/documents**
2. Click **"Try it out"**
3. Enter your RAG `conversation_id`
4. Click **"Choose File"** and select a PDF, DOCX, or TXT file (max 10MB)
5. Click **"Execute"**

**Expected Response:**
```json
{
  "_id": "...",
  "conversation_id": "...",
  "filename": "document.pdf",
  "file_size": 245632,
  "content_type": "application/pdf",
  "chunks_count": 15,
  "created_at": "2024-01-20T10:35:00Z"
}
```

#### 6c. Ask Questions About the Document

1. Find **POST /api/v1/conversations/{conversation_id}/messages**
2. Click **"Try it out"**
3. Enter your RAG `conversation_id`
4. Request body:
```json
{
  "content": "What are the main topics covered in this document?"
}
```
5. Click **"Execute"**

The AI response will be based on the uploaded document content!

#### 6d. List Documents in Conversation

1. Find **GET /api/v1/conversations/{conversation_id}/documents**
2. Click **"Try it out"**
3. Enter your `conversation_id`
4. Click **"Execute"**

### Step 7: Delete a Conversation

1. Find **DELETE /api/v1/conversations/{conversation_id}**
2. Click **"Try it out"**
3. Enter the `conversation_id` you want to delete
4. Click **"Execute"**
5. Should return **204 No Content** on success


## Key Features Explained

### Context Management

The system uses a two-tier approach:

1. **Sliding Window**: Keeps last 12 messages (configurable via `MAX_CONVERSATION_HISTORY`)
2. **Token Budget**: Maximum 7000 tokens (configurable via `MAX_TOKENS`)

If conversation exceeds limits:
- System messages are always preserved
- Most recent messages are prioritized
- Older messages are truncated automatically

### RAG Implementation

**Document Processing:**
1. Extract text from PDF/DOCX/TXT
2. Split into chunks (600 words with 100-word overlap)
3. Store chunks in MongoDB

**Retrieval:**
1. Calculate Jaccard similarity between query and chunks
2. Return top 3 most relevant chunks
3. Include chunks in LLM prompt with citations

**Response Generation:**
- System prompt instructs AI to cite document excerpts
- Context included before conversation history
- AI response indicates which excerpts were used

### Supported File Types

- **PDF**: `application/pdf` (via PyPDF2)
- **DOCX**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (via python-docx)
- **TXT**: `text/plain` (UTF-8 encoding)
- **Max file size**: 10MB

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful GET/PUT request
- **201 Created**: Successful POST request
- **204 No Content**: Successful DELETE request
- **400 Bad Request**: Invalid input (unsupported file type, invalid data)
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Server-side error

Error response format:
```json
{
  "detail": "Error message explaining what went wrong"
}
```

## Troubleshooting


**For MongoDB Atlas:**
- Verify connection string in `.env`
- Check IP whitelist in Atlas dashboard
- Ensure database user has correct permissions

### "Module not found" errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or recreate virtual environment
conda deactivate
rm -rf venv
conda create -p venv python==3.12
conda activate venv/
pip install -r requirements.txt
```


### Document upload fails

- **Check file size**: Maximum 10MB
- **Verify file type**: Only PDF, DOCX, TXT supported
- **Check logs**: Look for extraction errors
- **Try simpler document**: Some PDFs have complex formatting


## Dependencies

Core dependencies (from `requirements.txt`):

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **motor**: Async MongoDB driver
- **pymongo**: MongoDB operations
- **groq**: LLM API client
- **pydantic**: Data validation
- **tiktoken**: Token counting
- **pypdf**: PDF text extraction
- **python-docx**: DOCX text extraction

---

