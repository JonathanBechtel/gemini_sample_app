from typing import Any, List, Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import user
from app.api import deps
from app.db.models import User # If needed for type hints

router = APIRouter()

@router.get("/me", response_model=user.User)
async def read_users_me(
    current_user: Annotated[User, Depends(deps.get_current_active_user)]
) -> Any:
    """
    Get current user.
    """
    # User object is already fetched and validated by the dependency
    return current_user

# Optional: Endpoint to get all users (requires admin privileges usually)
# @router.get("/", response_model=List[schemas.User])
# async def read_users(
#     db: Annotated[AsyncSession, Depends(deps.get_db)],
#     skip: int = 0,
#     limit: int = 100,
#     # Add dependency for checking admin role here
#     # current_user: models.User = Depends(deps.get_current_admin_user),
# ) -> Any:
#     """
#     Retrieve users. (Requires admin rights - not implemented here)
#     """
#     users = await crud.crud_user.get_users(db, skip=skip, limit=limit)
#     return users