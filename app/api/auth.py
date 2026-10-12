from typing import Annotated

from fastapi import APIRouter, Depends, status, Form, HTTPException, Response, Request
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.core.database import get_db
from app.core.oauth2 import get_access_token_data
from app.repositories import auth_repository
from app.schemas.auth_schema import (
    SignUpSchema, LoginSchema, AfterSignUpSchema, AfterLoginSchema, Token, TokenData, UserReadSchema
)


router = APIRouter(
    prefix="/api/auth", tags=["Auth"]
)


@router.post('/register', response_model=AfterSignUpSchema, status_code=status.HTTP_201_CREATED)
def signup_route(data: SignUpSchema, db: Session = Depends(get_db)):
    user = auth_repository.signup(data, db)
    return {"user": user, "message": "User created successfully"}


@router.post('/login', response_model=AfterLoginSchema, status_code=status.HTTP_200_OK)
def login_route(
    request: Request,
    response: Response,
    username: str | None = Form(None),
    email: EmailStr | None = Form(None),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not username and not email:
        raise HTTPException(status_code=400, detail="Username or email required")

    schema = LoginSchema(login=username or email or '', password=password)
    client_ip = request.client.host if request.client else "unknown"
    user, access_token = auth_repository.login(schema, db, response, client_ip)
    
    return {"user": UserReadSchema.model_validate(user), "access_token": access_token, "token_type": "bearer"}


@router.post('/refresh', response_model=Token, status_code=status.HTTP_200_OK)
def refresh_route(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    new_access_token = auth_repository.refresh(request, response, db)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post('/logout', status_code=status.HTTP_200_OK)
def logout_route(
    request: Request,
    response: Response,
    access_token_data: Annotated[TokenData, Depends(get_access_token_data)]
):
    auth_repository.logout(request, response, access_token_data)
    return {"message": "Logged out successfully"}


@router.post('/logout-all', status_code=status.HTTP_200_OK)
def logout_all_route(
    response: Response,
    access_token_data: Annotated[TokenData, Depends(get_access_token_data)]
):
    auth_repository.logout_all(response, access_token_data)
    return {"message": "Logged out from all devices successfully"}