from pydantic import BaseModel, EmailStr, ConfigDict


class SignUpSchema(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str
    bio: str


class LoginSchema(BaseModel):
    login: str | EmailStr
    password: str


class ProfileReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bio: str


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    username: str
    email: EmailStr
    profile: ProfileReadSchema 


class AfterSignUpSchema(BaseModel):
    message: str
    user: UserReadSchema


class Token(BaseModel):
    access_token: str
    token_type: str


class AfterLoginSchema(Token):
    user: UserReadSchema


class TokenData(BaseModel):
    sub: int
    type: str
    role: str
    family_id: str | None = None
    exp: int
    iat: int
    jti: str