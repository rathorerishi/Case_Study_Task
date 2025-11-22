
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    # MongoDB connection manager
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Establish connection to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            # Verify connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {settings.mongodb_url}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")
    
    @classmethod
    def get_database(cls):
        """Get database instance"""
        if not cls.client:
            raise Exception("Database not connected. Call connect_db() first.")
        return cls.client[settings.mongodb_db_name]


# Collection names constants
class Collections:
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    DOCUMENTS = "documents"




async def create_indexes():
    db = MongoDB.get_database()
    
    # Conversations collection indexes
    await db[Collections.CONVERSATIONS].create_index("user_id")
    await db[Collections.CONVERSATIONS].create_index("created_at")
    
    # Messages collection indexes
    await db[Collections.MESSAGES].create_index([
        ("conversation_id", 1),
        ("sequence_number", 1)
    ], unique=True)
    await db[Collections.MESSAGES].create_index("conversation_id")
    
    # Documents collection indexes
    await db[Collections.DOCUMENTS].create_index("conversation_id")
    
    logger.info("Database indexes created successfully")