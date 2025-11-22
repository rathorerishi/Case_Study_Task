
# Main FastAPI application.
# Entry point for the BOT GPT backend service.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.api.routes import router
from app.database.mongodb import MongoDB, create_indexes
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Lifecycle manager for FastAPI application.
    # Handles startup and shutdown events.
    
    # Startup
    logger.info("Starting BOT GPT backend...")
    try:
        # Connect to MongoDB
        await MongoDB.connect_db()
        
        # Create database indexes
        await create_indexes()
        
        logger.info("BOT GPT backend started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down BOT GPT backend...")
    await MongoDB.close_db()
    logger.info("BOT GPT backend shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="BOT GPT API",
    description="Production-grade conversational AI backend with RAG support",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    #Root endpoint.
    return {
        "message": "BOT GPT API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )