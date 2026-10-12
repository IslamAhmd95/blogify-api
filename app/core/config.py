import os
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    # fail at startup instead of silently running with a missing/placeholder value
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Settings:
    SECRET_KEY = _required("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # refresh token cookie: use COOKIE_SAMESITE=none (+ COOKIE_SECURE=true) when the frontend is on another domain
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "strict")

    # brute force protection: max failed logins per (ip, login) within the window
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", 5))
    LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", 15 * 60))

settings = Settings()
