from typing import Any, Dict, Optional, Union, List
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sqlalchemy_update

from app.core.security import get_password_hash, verify_password
from app.db.models import User, UserOAuthAccount
from app.schemas.user import UserCreate, UserUpdate, UserOAuthInfo

# Basic CRUD operations for User model

async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).filter(User.user_id == user_id))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, *, obj_in: UserCreate) -> User:
    hashed_password = get_password_hash(obj_in.password)
    db_obj = User(
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=hashed_password,
        # Default status is set in the model
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_user(db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True) # Use model_dump in Pydantic v2

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    elif "password" in update_data: # Handle case where password might be None or empty string
        del update_data["password"]

    # Update fields
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def authenticate_user(db: AsyncSession, *, username_or_email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email=username_or_email)
    if not user and "@" not in username_or_email: # Try username if email failed and it looks like a username
         user = await get_user_by_username(db, username=username_or_email)

    if not user:
        return None
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_or_create_oauth_user(db: AsyncSession, *, oauth_info: UserOAuthInfo) -> User:
    # 1. Check if OAuth account exists
    query = select(UserOAuthAccount).where(
        UserOAuthAccount.provider_name == oauth_info.provider_name,
        UserOAuthAccount.provider_user_id == oauth_info.provider_user_id
    ).limit(1)
    result = await db.execute(query)
    oauth_account = result.scalars().first()

    if oauth_account:
        # Update last login maybe?
        # stmt = (
        #     sqlalchemy_update(User)
        #     .where(User.user_id == oauth_account.user_id)
        #     .values(last_login_at=func.now())
        # )
        # await db.execute(stmt)
        # await db.commit()
        return await get_user(db, oauth_account.user_id) # Return existing user

    # 2. Check if user with this email already exists
    user = await get_user_by_email(db, email=oauth_info.email)

    if user:
        # User exists, link the new OAuth account to them
        db_oauth_account = UserOAuthAccount(
            user_id=user.user_id,
            provider_name=oauth_info.provider_name,
            provider_user_id=oauth_info.provider_user_id,
        )
        db.add(db_oauth_account)
        # Optionally mark email as verified if provider guarantees it
        if not user.email_verified:
            user.email_verified = True
            db.add(user)

        await db.commit()
        await db.refresh(user)
        return user
    else:
        # 3. Create new user and link OAuth account
        new_user = User(
            email=oauth_info.email,
            username=oauth_info.username, # Might need generation if null/duplicate
            email_verified=True, # Assume verified from provider
            status=UserStatus.active # Directly activate OAuth users
            # hashed_password is None
        )
        db.add(new_user)
        await db.flush() # Flush to get the new_user.user_id

        db_oauth_account = UserOAuthAccount(
            user_id=new_user.user_id,
            provider_name=oauth_info.provider_name,
            provider_user_id=oauth_info.provider_user_id,
        )
        db.add(db_oauth_account)
        await db.commit()
        await db.refresh(new_user)
        return new_user