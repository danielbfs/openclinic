"""JWT token management, password hashing, and refresh-token blocklist."""
import logging
import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

_redis: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def is_refresh_token_revoked(jti: str) -> bool:
    """Check if a refresh token's jti is in the Redis blocklist."""
    if not jti:
        return False
    try:
        r = await _get_redis()
        return bool(await r.exists(f"revoked:refresh:{jti}"))
    except Exception:
        logger.exception("Redis check failed for refresh jti %s", jti)
        # Fail open — Redis indisponível não deve bloquear todos os logins
        return False


async def revoke_refresh_token(payload: dict) -> bool:
    """Add a refresh token's jti to the Redis blocklist until it expires."""
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return False
    try:
        ttl = int(exp - datetime.now(timezone.utc).timestamp())
        if ttl <= 0:
            return True  # already expired
        r = await _get_redis()
        await r.setex(f"revoked:refresh:{jti}", ttl, "1")
        return True
    except Exception:
        logger.exception("Failed to revoke refresh token jti %s", jti)
        return False
