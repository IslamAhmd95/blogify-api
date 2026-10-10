import redis

from app.core.config import settings


redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def blacklist_access_token(jti: str, ttl: int):
    if ttl > 0:
        redis_client.setex(f"blacklist:{jti}", ttl, 1)


def revoke_refresh_token(jti: str, ttl: int):
    if ttl > 0:
        redis_client.setex(f"revoked:{jti}", ttl, 1)


def revoke_refresh_tokens_family(family_id: str, ttl: int):
    if ttl > 0:
        redis_client.setex(f"revoked_family:{family_id}", ttl, 1)


def is_access_token_blacklisted(jti: str) -> bool:
    return redis_client.exists(f"blacklist:{jti}") == 1


def is_refresh_token_revoked(jti: str) -> bool:
    return redis_client.exists(f"revoked:{jti}") == 1


def is_refresh_tokens_family_revoked(family_id: str) -> bool:
    return redis_client.exists(f"revoked_family:{family_id}") == 1
