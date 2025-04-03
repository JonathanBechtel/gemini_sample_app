from pydantic import BaseModel, EmailStr, Field
import uuid
from datetime import datetime
from typing import Optional

from app.db.models import UserStatus # Import the enum

# Base properties shared by all user schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: Optional[str] = Field(None, min_length=3, max_length=50, example="john_doe")

# Properties required during user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="S3cureP@ssw0rd")

# Properties received via API on update (optional fields)
class UserUpdate(UserBase):
    email: Optional[EmailStr] = None # Allow email update (needs verification flow usually)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8) # For password change

# Properties stored in DB but not always returned to client
class UserInDBBase(UserBase):
    user_id: uuid.UUID
    email_verified: bool = False
    status: UserStatus = UserStatus.pending_verification
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replaces orm_mode=True in Pydantic v2

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: Optional[str] = None

# Properties returned to client (public representation)
class User(UserInDBBase):
    pass # Inherits public fields from UserInDBBase

# Schema for OAuth User Info (example)
class UserOAuthInfo(BaseModel):
    provider_name: str
    provider_user_id: str
    email: EmailStr
    username: Optional[str] = None