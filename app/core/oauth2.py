from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.models.user import User
from app.core.token import verify_token, credentials_exception
from app.schemas.auth_schema import TokenData


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_access_token_data(token_str: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    return verify_token(token_str, expected_type="access")


def get_current_user(
    token_data: Annotated[TokenData, Depends(get_access_token_data)],
    db: Session = Depends(get_db)
) -> User:

    user = db.scalar(select(User).where(User.id == token_data.sub))
    if user is None:
        raise credentials_exception

    return user
