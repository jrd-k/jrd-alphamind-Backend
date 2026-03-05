import redis

from app.core.config import settings

# simple wrapper to allow dependency injection and reuse
class RedisService:
    def __init__(self):
        # use lowercase attribute defined in config
        self.redis = redis.from_url(settings.redis_url)


redis_service = RedisService()