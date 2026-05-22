from sqlmodel import SQLModel, Field, Column, Relationship,String
from typing import Optional,List

class Token(SQLModel,table=False):
    access_token: str
    token_type: str


class TokenData(SQLModel,table=False):
    email: str | None = None


class User(SQLModel,table=False):
    username: str = Field(min_length=5)
    email: str = Field(unique=True, index=True,  primary_key=True)

    full_name:  Optional[str] = Field(default=None, min_length=5)
    disabled: bool = Field(default=None)


class UserInDB(User,table=True):
    hashed_password: str
