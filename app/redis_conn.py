import aioredis

from environ import REDIS_PORT, REDIS_HOST


redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
