import time

import redis

from app.core.config import settings


redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

REFRESH_TOKEN_EXPIRE_SECONDS = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def blacklist_access_token(jti: str, ttl: int):
    if ttl > 0:
        redis_client.setex(f"blacklist:{jti}", ttl, 1)


def revoke_refresh_token(jti: str, ttl: int) -> bool:
    """Returns True if this call revoked the token, False if it was already revoked.
    SET NX is atomic, so if two requests race with the same token only one of them wins."""
    if ttl <= 0:
        return True
    return bool(redis_client.set(f"revoked:{jti}", 1, ex=ttl, nx=True))


def revoke_refresh_tokens_family(family_id: str, ttl: int):
    if ttl > 0:
        redis_client.setex(f"revoked_family:{family_id}", ttl, 1)


def revoke_all_user_tokens(user_id: int):
    # every token of this user issued before this moment becomes invalid (logout from all devices).
    # +1 because iat has second precision: a token issued earlier in this same second must be rejected too.
    # TTL = longest token lifetime, after that every old token is expired anyway
    redis_client.setex(f"tokens_valid_after:{user_id}", REFRESH_TOKEN_EXPIRE_SECONDS, int(time.time()) + 1)


def get_user_tokens_valid_after(user_id: int) -> int | None:
    value = redis_client.get(f"tokens_valid_after:{user_id}")
    return int(value) if value else None


def is_access_token_blacklisted(jti: str) -> bool:
    return redis_client.exists(f"blacklist:{jti}") == 1


def is_refresh_token_revoked(jti: str) -> bool:
    return redis_client.exists(f"revoked:{jti}") == 1


def is_refresh_tokens_family_revoked(family_id: str) -> bool:
    return redis_client.exists(f"revoked_family:{family_id}") == 1


def is_login_locked(key: str) -> bool:
    attempts = redis_client.get(f"login_attempts:{key}")
    return attempts is not None and int(attempts) >= settings.LOGIN_MAX_ATTEMPTS


def register_failed_login(key: str):
    attempts_key = f"login_attempts:{key}"
    attempts = redis_client.incr(attempts_key)
    if attempts == 1:
        # the window starts at the first failure
        redis_client.expire(attempts_key, settings.LOGIN_LOCKOUT_SECONDS)


def reset_failed_logins(key: str):
    redis_client.delete(f"login_attempts:{key}")
