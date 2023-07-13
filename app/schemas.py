from uuid import UUID

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, constr


class TokenData(BaseModel):
    uuid: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    uuid: UUID
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    published: bool


class PostResponse(PostBase):
    author_id: UUID
    id: int
    created_at: datetime
    rating: int

    model_config = ConfigDict(from_attributes=True)

