import uuid
from pydantic import BaseModel, Field

class Book(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    title: str = Field(...)
    author: str = Field(...)
    description: str = Field(...)
    genre: str = Field(...)
    cover_img: str = Field(...)
    text_path: str = Field(...)