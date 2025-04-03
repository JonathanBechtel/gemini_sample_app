from pydantic import BaseModel
import uuid

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: uuid.UUID | None = None # Subject (user_id)