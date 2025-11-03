from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    """
    Schema for incoming requests to create a new user.
    """
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = None

class UserLogin(BaseModel):
    """
    Schema for incoming requests to log in a user.
    """
    username: str
    password: str

class UserResponse(BaseModel):
    """
    Schema for sending user data back in API responses.
    """
    id: int
    username: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True