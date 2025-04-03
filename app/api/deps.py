from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db.base import get_db # Import async get_db
from app.db.models import User
from app.schemas.token import TokenData
from app.crud import crud_user

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token" # Matches the login endpoint path
)

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
        if payload is None:
            raise credentials_exception
        token_data = TokenData(**payload) # Validate payload structure

        if token_data.sub is None:
            raise credentials_exception

    except (JWTError, ValidationError):
         raise credentials_exception

    user = await crud_user.get_user(db, user_id=token_data.sub)
    if user is None:
        raise credentials_exception
    # Add checks for user status if needed (e.g., if not user.is_active:)
    # if user.status != UserStatus.active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return user

# Dependency for getting the current active user (can add more checks)
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    # Example check:
    # if current_user.status != UserStatus.active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user