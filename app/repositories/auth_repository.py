from fastapi import status, HTTPException, Response, Request
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.token import (
    create_token, verify_token, get_remaining_ttl, credentials_exception, REFRESH_TOKEN_EXPIRE_SECONDS
)
from app.core.token_store import (
    blacklist_access_token, revoke_refresh_token, revoke_refresh_tokens_family, revoke_all_user_tokens,
    is_login_locked, register_failed_login, reset_failed_logins
)
from app.models.user import User
from app.models.profile import Profile
from app.core.hashing import hash_password, verify_password, DUMMY_PASSWORD_HASH
from app.schemas.auth_schema import SignUpSchema, LoginSchema, TokenData
from app.core.helpers import (
    check_email_exists, check_username_exists, refresh_token_set_cookie, refresh_token_delete_cookie,
    REFRESH_TOKEN_COOKIE_NAME
)


def signup(data: SignUpSchema, db: Session):
    if check_email_exists(data.email, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if check_username_exists(data.username, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    user_data = data.model_dump()
    bio = user_data.pop('bio')
    user_data['password'] = hash_password(user_data['password'])

    user = User(**user_data)
    user.profile = Profile(bio=bio)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


def login(data: LoginSchema, db: Session, response: Response, client_ip: str):
    # brute force protection, keyed by ip + login so one attacker can't lock everyone out of an account
    attempts_key = f"{client_ip}:{data.login.lower()}"
    if is_login_locked(attempts_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts, try again later"
        )

    user = db.scalar(select(User).where(or_(
        User.email == data.login, User.username == data.login)))

    # same error (and same timing, via the dummy hash) for unknown user and wrong password, so the response doesn't reveal which accounts exist
    password_hash = user.password if user and user.password else DUMMY_PASSWORD_HASH
    password_ok = verify_password(data.password, password_hash)
    if not user or not user.password or not password_ok:
        register_failed_login(attempts_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    reset_failed_logins(attempts_key)

    # JWT "sub" must be a string (PyJWT >= 2.10 rejects non-string subjects)
    access_token = create_token(
        data={"sub": str(user.id), "role": user.role},
        type="access"
    )
    refresh_token = create_token(
        data={"sub": str(user.id), "role": user.role},
        type="refresh"
    )

    refresh_token_set_cookie(refresh_token, response)
    
    return user, access_token


def refresh(request: Request, response: Response, db: Session):
    old_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not old_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token missing"
        )
        
    token_data = verify_token(old_refresh_token, expected_type="refresh")

    # load the user so a deleted user can't refresh and a changed role is picked up
    user = db.get(User, token_data.sub)
    if user is None:
        raise credentials_exception

    # rotation: the old refresh token can never be used again.
    # verify_token already checked it isn't revoked, but two requests with the same token can both pass
    # that check; revoking is atomic, so if we lose the race this is a reuse
    if not revoke_refresh_token(token_data.jti, get_remaining_ttl(token_data.exp)):
        if token_data.family_id:
            revoke_refresh_tokens_family(token_data.family_id, REFRESH_TOKEN_EXPIRE_SECONDS)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    new_access_token = create_token(
        data={"sub": str(user.id), "role": user.role},
        type="access"
    )
    new_refresh_token = create_token(
        data={"sub": str(user.id), "role": user.role},
        type="refresh",
        family_id=token_data.family_id
    )

    refresh_token_set_cookie(new_refresh_token, response)

    return new_access_token
    
    
def logout(request: Request, response: Response, access_token_data: TokenData):
    # blacklist the access token
    blacklist_access_token(access_token_data.jti, get_remaining_ttl(access_token_data.exp))

    # revoke the refresh token if there is a valid one, logout must still succeed if not
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        try:
            refresh_token_data = verify_token(refresh_token, expected_type="refresh")
        except HTTPException:
            refresh_token_data = None   # expired, revoked or invalid: nothing left to revoke

        if refresh_token_data and refresh_token_data.sub == access_token_data.sub:
            revoke_refresh_token(refresh_token_data.jti, get_remaining_ttl(refresh_token_data.exp))
            if refresh_token_data.family_id:
                revoke_refresh_tokens_family(refresh_token_data.family_id, REFRESH_TOKEN_EXPIRE_SECONDS)

    refresh_token_delete_cookie(response)


def logout_all(response: Response, access_token_data: TokenData):
    # invalidates every access and refresh token of the user, on every device
    revoke_all_user_tokens(access_token_data.sub)
    refresh_token_delete_cookie(response)
