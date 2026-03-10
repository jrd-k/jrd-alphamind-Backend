import redis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# simple wrapper to allow dependency injection and reuse
class RedisService:
    def __init__(self):
        try:
            # use lowercase attribute defined in config
            self.redis = redis.from_url(settings.redis_url)
            # Test the connection
            self.redis.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. WebSocket features will work without Redis.")
            self.redis = None


redis_service = RedisService()