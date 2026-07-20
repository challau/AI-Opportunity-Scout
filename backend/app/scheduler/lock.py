"""Redis distributed locking mechanism for scheduler coordination."""

import uuid
from typing import Optional, Tuple
import structlog
import redis.asyncio as aioredis

logger = structlog.get_logger()

LOCK_KEY = "scheduler:instance_lock"
# Generate a unique ID for this app/worker instance
INSTANCE_ID = str(uuid.uuid4())

# Lua scripts for atomic operations
RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

REFRESH_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
else
    return 0
end
"""

async def acquire_lock(redis_client: aioredis.Redis, ttl_seconds: int) -> bool:
    """
    Attempt to acquire the scheduler lock.
    Returns True if successfully acquired, False otherwise.
    """
    try:
        # ex=ttl_seconds defines expiration in seconds, nx=True sets key only if not exists
        acquired = await redis_client.set(LOCK_KEY, INSTANCE_ID, ex=ttl_seconds, nx=True)
        if acquired:
            logger.info("Scheduler lock acquired", instance_id=INSTANCE_ID, key=LOCK_KEY)
            return True
        return False
    except Exception as e:
        logger.error("Error acquiring scheduler lock", error=str(e))
        return False

async def release_lock(redis_client: aioredis.Redis) -> bool:
    """
    Release the scheduler lock if held by this instance.
    Returns True if successfully released, False otherwise.
    """
    try:
        result = await redis_client.eval(RELEASE_LUA, 1, LOCK_KEY, INSTANCE_ID)
        if result == 1:
            logger.info("Scheduler lock released", instance_id=INSTANCE_ID)
            return True
        return False
    except Exception as e:
        logger.error("Error releasing scheduler lock", error=str(e))
        return False

async def refresh_lock(redis_client: aioredis.Redis, ttl_seconds: int) -> bool:
    """
    Refresh the lock's expiration if held by this instance.
    Returns True if successfully refreshed, False otherwise.
    """
    try:
        result = await redis_client.eval(REFRESH_LUA, 1, LOCK_KEY, INSTANCE_ID, ttl_seconds)
        if result == 1:
            logger.debug("Scheduler lock refreshed", instance_id=INSTANCE_ID)
            return True
        logger.warning("Scheduler lock refresh failed (not held or expired)", instance_id=INSTANCE_ID)
        return False
    except Exception as e:
        logger.error("Error refreshing scheduler lock", error=str(e))
        return False

async def get_lock_info(redis_client: aioredis.Redis) -> Tuple[Optional[str], int]:
    """
    Get current lock owner and its remaining time-to-live in seconds.
    Returns (owner_id, ttl). If lock is not held, returns (None, -2).
    """
    try:
        owner = await redis_client.get(LOCK_KEY)
        ttl = await redis_client.ttl(LOCK_KEY)
        return owner, ttl
    except Exception as e:
        logger.error("Error getting lock info", error=str(e))
        return None, -1
