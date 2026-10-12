from datetime import datetime, timedelta, timezone
import uuid

from fastapi import HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from pydantic import ValidationError

from app.core.config import settings
from app.core.token_store import (
    is_access_token_blacklisted, is_refresh_token_revoked, is_refresh_tokens_family_revoked,
    revoke_refresh_tokens_family, get_user_tokens_valid_after, REFRESH_TOKEN_EXPIRE_SECONDS
)
from app.schemas.auth_schema import TokenData


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def __issue_token(type: str, family_id : str | None = None):
    now = datetime.now(timezone.utc)
    payload = {}

    expire = int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    if type == "refresh":
        expire = int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
        if not family_id:
            family_id = str(uuid.uuid4())
        payload["family_id"] = family_id

    jti = str(uuid.uuid4())
    iat = int(now.timestamp())

    payload.update({
        "type": type,
        "exp": expire,
        "jti": jti,
        "iat": iat
    })

    return payload


def create_token(data: dict, type: str, family_id: str | None = None):
    to_encode = data.copy()
    payload = __issue_token(type=type, family_id=family_id)
    to_encode.update(payload)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_remaining_ttl(exp: int) -> int:
    return exp - int(datetime.now(timezone.utc).timestamp())


def verify_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
    except ExpiredSignatureError:
        # a distinct message so the frontend knows it should call /refresh
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except (InvalidTokenError, ValidationError):
        raise credentials_exception

    if token_data.type != expected_type:
        raise credentials_exception

    # logout from all devices / password change: reject every token issued before that moment
    valid_after = get_user_tokens_valid_after(token_data.sub)
    if valid_after and token_data.iat < valid_after:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been terminated, please log in again"
        )

    if expected_type == "refresh":
        if token_data.family_id and is_refresh_tokens_family_revoked(token_data.family_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

        if is_refresh_token_revoked(token_data.jti):
            # an already rotated token is being reused, so it may have been stolen: kill the whole family
            if token_data.family_id:
                revoke_refresh_tokens_family(token_data.family_id, REFRESH_TOKEN_EXPIRE_SECONDS)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

    elif expected_type == "access":
        if is_access_token_blacklisted(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is blacklisted"
            )

    return token_data
