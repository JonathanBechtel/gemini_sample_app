from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.models import User # Import User model if needed for type hinting or direct use

router = APIRouter()

@router.post("/register", response_model=schemas.User)
async def register_user(
    *,
    db: Annotated[AsyncSession, Depends(deps.get_db)],
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = await crud.crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )
    if user_in.username:
        user = await crud.crud_user.get_user_by_username(db, username=user_in.username)
        if user:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this username already exists.",
             )
    try:
        user = await crud.crud_user.create_user(db=db, obj_in=user_in)
        # Add email verification logic here if desired (send email)
        return user
    except IntegrityError: # Catch potential race condition duplicates
         await db.rollback()
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists with this email or username.",
         )


@router.post("/login/access-token", response_model=schemas.Token)
async def login_for_access_token(
    response: Response, # Inject Response object to set cookie
    db: Annotated[AsyncSession, Depends(deps.get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Uses username or email.
    """
    user = await crud.crud_user.authenticate_user(
        db, username_or_email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Add checks for user status (e.g., email verified, active)
    # elif user.status != UserStatus.active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.user_id, expires_delta=access_token_expires
    )

    # Set token in an HTTPOnly cookie (optional, common for web apps)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()), # Required for max_age
        # secure=True,  # Should be True in production (HTTPS)
        # samesite="lax" # Or "strict"
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    """
    Removes the access token cookie.
    Note: This doesn't invalidate the JWT itself (stateless).
    Proper logout requires server-side token management (e.g., blocklist).
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


# --- OAuth Stubs ---

@router.get("/login/oauth/{provider}")
async def oauth_login(provider: str):
    """
    Redirects the user to the OAuth provider's authorization page. (STUB)
    """
    # In a real app:
    # 1. Get provider config (client_id, redirect_uri, scopes, auth_url)
    # 2. Generate state parameter for CSRF protection (store in session/cache)
    # 3. Construct the authorization URL
    # 4. Return RedirectResponse(auth_url)
    allowed_providers = ["google", "github"] # Example
    if provider not in allowed_providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not supported")

    # Placeholder - replace with actual redirect logic
    # from fastapi.responses import RedirectResponse
    # state = "generate_random_state_here"
    # auth_url = f"https://provider.com/auth?client_id=YOUR_ID&redirect_uri=YOUR_URI&scope=SCOPES&state={state}&response_type=code"
    # return RedirectResponse(auth_url)

    return {"message": f"Redirect to {provider} OAuth page (Not Implemented)", "provider": provider}


@router.get("/callback/oauth/{provider}")
async def oauth_callback(
    provider: str,
    code: str | None = None,  # Authorization code from provider
    state: str | None = None, # State for CSRF check
    error: str | None = None, # Optional error from provider
    error_description: str | None = None,
    db: Annotated[AsyncSession, Depends(deps.get_db)],
    response: Response,
):
    """
    Handles the callback from the OAuth provider after user authorization. (STUB)
    """
    allowed_providers = ["google", "github"] # Example
    if provider not in allowed_providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not supported")

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth Error: {error} - {error_description}")

    if not code:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    # In a real app:
    # 1. Verify 'state' parameter against stored value (CSRF protection)
    # 2. Exchange 'code' for an access token with the provider (POST request to token URL)
    # 3. Use provider's access token to fetch user profile info (email, name, provider ID)
    # 4. Map provider info to `schemas.UserOAuthInfo`
    # 5. Use `crud.crud_user.get_or_create_oauth_user(db, oauth_info=...)` to get/create local user
    # 6. Create an internal JWT for your application (`security.create_access_token`)
    # 7. Set the JWT cookie (like in password login)
    # 8. Redirect user to the frontend application (e.g., dashboard) or return token

    # Placeholder - replace with actual OAuth flow logic
    print(f"Received callback from {provider} with code: {code}, state: {state}")

    # --- Placeholder user creation ---
    # Simulate fetching user info from provider
    mock_user_info = schemas.UserOAuthInfo(
        provider_name=provider,
        provider_user_id=f"{provider}_{uuid.uuid4()}", # Fake provider ID
        email=f"user_{uuid.uuid4()}@{provider}.example.com", # Fake email
        username=f"{provider}_user_{uuid.uuid4()}"
    )
    try:
        user = await crud.crud_user.get_or_create_oauth_user(db=db, oauth_info=mock_user_info)
    except Exception as e:
        # Log the error
        print(f"Error during OAuth user processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to process OAuth login")

    # --- Issue internal token ---
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.user_id, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
         max_age=int(access_token_expires.total_seconds()),
        # secure=True,
        # samesite="lax"
    )

    # Option 2: Redirect to frontend (common for traditional web flows)
    from fastapi.responses import RedirectResponse
    frontend_url = "http://localhost:3000/dashboard?login=success" # Example redirect
    return RedirectResponse(frontend_url)

    # Option 3: Return a simple message after setting cookie
    # return {"message": f"Successfully authenticated via {provider}. Token set in cookie."}