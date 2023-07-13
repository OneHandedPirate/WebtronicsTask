import aioredis

from environ import REDIS_PORT, REDIS_HOST, REDIS_DB


redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
