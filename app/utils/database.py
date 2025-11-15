import sqlite3
import redis.asyncio as redis
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Global database connection
db_connection = None

# Global Redis client
redis_client = None


async def init_db():
    """Initialize database connections"""
    global db_connection, redis_client
    
    try:
        # Create SQLite connection
        db_path = settings.DATABASE_URL.replace("file:", "")
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
        logger.info(f"SQLite database connected successfully at {db_path}")
        
        # Try to connect to Redis (optional for now)
        try:
            redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("Redis connected successfully")
        except Exception as redis_error:
            logger.warning(f"Redis connection failed (optional): {str(redis_error)}")
            redis_client = None
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        # Don't raise - allow server to start without Redis
        pass


async def disconnect_db():
    """Disconnect database connections"""
    global db_connection, redis_client
    
    try:
        if db_connection:
            db_connection.close()
            logger.info("SQLite database disconnected")
        
        if redis_client:
            await redis_client.close()
            logger.info("Redis disconnected")
            
    except Exception as e:
        logger.error(f"Database disconnection failed: {str(e)}")


def get_db():
    """Get database instance"""
    return db_connection


def get_redis():
    """Get Redis instance"""
    return redis_client
