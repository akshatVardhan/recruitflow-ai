import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    # The refresh token itself never appears in a JSON body - it's set as an
    # httpOnly cookie so JS can't read it (frontend/lib/api.ts's interceptor
    # already assumed this cookie-based flow before the backend existed).
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
