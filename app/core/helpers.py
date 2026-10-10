from typing import Optional

from fastapi import Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.models.user import User
from app.core.enums import RoleEnum
from app.core.config import settings


REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
# shared by set_cookie and delete_cookie: the browser only deletes a cookie if these match
REFRESH_TOKEN_COOKIE_OPTIONS = {
    "httponly": True,       # Prevents JS from reading it (Blocks XSS)
    "secure": True,         # Requires HTTPS
    "samesite": "strict",   # Blocks cross-site request forgery (CSRF)
    "path": "/api/auth",    # Browser only sends it to the auth routes (refresh, logout)
}


def check_email_exists(email: str, db: Session, user: Optional[User] = None):
    query = select(User).where(User.email == email)
    if user:
        query = query.where(User.id != user.id)

    return db.execute(query).scalar()


def check_username_exists(username: str, db: Session, user: Optional[User] = None):
    query = select(User).where(User.username == username)
    if user:
        query = query.where(User.id != user.id)

    return db.execute(query).scalar()


def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def refresh_token_set_cookie(refresh_token, response: Response):
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **REFRESH_TOKEN_COOKIE_OPTIONS
    )


def refresh_token_delete_cookie(response: Response):
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, **REFRESH_TOKEN_COOKIE_OPTIONS)
