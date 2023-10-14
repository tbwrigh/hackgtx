import uuid
from pydantic import BaseModel, Field

class Book(BaseModel):
    book_id: str = Field(default_factory=uuid.uuid4, alias="_id")
    title: str = Field(...)
    author: str = Field(...)
    description: str = Field(...)
    genre: str = Field(...)



class User(BaseModel):
    user_id: str = Field(default_factory=uuid.uuid4, alias="_id")
    username: str = Field(...)
    email: str = Field(...)
    password_hash: str = Field(...)
    admin: bool = Field(...)

class Section(BaseModel):
    section_id: str = Field(default_factory=uuid.uuid4, alias="_id")
    book_id: str = Field(...)
    user_id: str = Field(...)
    start: int = Field(...)
    end: int = Field(...)
    img_path: str = Field(...)

class Current(BaseModel):
    user_id: str = Field(...)
    book_id: str = Field(...)
    section_id: str = Field(...)