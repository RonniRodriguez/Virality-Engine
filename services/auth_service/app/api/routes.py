"""
Idea Inc - Auth Service API Routes

REST API endpoints for authentication and user management.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.config import get_settings
from shared.utils.logging import get_logger
from shared.utils.security import (
    create_token_pair,
    hash_password,
    verify_password,
    verify_token,
)

from app.api.schemas import (
    ErrorResponse,
    MessageResponse,
    PasswordChange,
    ProfileUpdate,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.db.database import get_db
from app.db.models import User

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Dependency to optionally get current user (for public endpoints)"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# =============================================================================
# Registration & Login
# =============================================================================

@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Register a new user with email and password.
    
    Returns access and refresh tokens on successful registration.
    """
    logger.info("Registration attempt", email=data.email)
    
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        logger.warning("Registration failed: email exists", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = User(
        email=data.email,
        display_name=data.display_name or data.email.split("@")[0],
        password_hash=hash_password(data.password),
        provider="local",
        roles=["player"],
        is_verified=False,  # Would need email verification in production
    )
    
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    logger.info("User registered", user_id=str(user.id), email=data.email)
    
    # Generate tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        roles=user.roles,
    )
    
    return TokenResponse(**tokens)


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(
    data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Login with email and password.
    
    Returns access and refresh tokens on successful authentication.
    """
    logger.info("Login attempt", email=data.email)
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        logger.warning("Login failed: user not found", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not verify_password(data.password, user.password_hash):
        logger.warning("Login failed: invalid password", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not user.is_active:
        logger.warning("Login failed: account disabled", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.flush()
    
    logger.info("User logged in", user_id=str(user.id), email=data.email)
    
    # Generate tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        roles=user.roles,
    )
    
    return TokenResponse(**tokens)


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def refresh_token(
    data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Refresh access token using refresh token.
    
    Returns new access and refresh tokens.
    """
    payload = verify_token(data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Find user
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    
    logger.info("Token refreshed", user_id=str(user.id))
    
    # Generate new tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        roles=user.roles,
    )
    
    return TokenResponse(**tokens)


@router.post(
    "/auth/logout",
    response_model=MessageResponse,
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Logout current user.
    
    In production, this would invalidate the refresh token.
    """
    logger.info("User logged out", user_id=str(current_user.id))
    
    # TODO: Add refresh token to blacklist/revoke in Redis
    
    return MessageResponse(message="Successfully logged out")


# =============================================================================
# User Profile
# =============================================================================

@router.get(
    "/auth/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/auth/me",
    response_model=UserResponse,
)
async def update_me(
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user profile"""
    if data.display_name is not None:
        current_user.display_name = data.display_name
    if data.bio is not None:
        current_user.bio = data.bio
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    
    await db.flush()
    await db.refresh(current_user)
    
    logger.info("Profile updated", user_id=str(current_user.id))
    
    return UserResponse.model_validate(current_user)


@router.post(
    "/auth/change-password",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}},
)
async def change_password(
    data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change current user password"""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth accounts",
        )
    
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    current_user.password_hash = hash_password(data.new_password)
    await db.flush()
    
    logger.info("Password changed", user_id=str(current_user.id))
    
    return MessageResponse(message="Password changed successfully")


# =============================================================================
# OAuth2 Routes (Stubs for MVP)
# =============================================================================

@router.get("/auth/oauth/google")
async def oauth_google_redirect():
    """Redirect to Google OAuth"""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )
    
    # TODO: Implement Google OAuth redirect
    return {"message": "Google OAuth redirect - not implemented in MVP"}


@router.get("/auth/callback/google")
async def oauth_google_callback(code: str, state: str | None = None):
    """Handle Google OAuth callback"""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )
    
    # TODO: Implement Google OAuth callback
    return {"message": "Google OAuth callback - not implemented in MVP"}


@router.get("/auth/oauth/github")
async def oauth_github_redirect():
    """Redirect to GitHub OAuth"""
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth not configured",
        )
    
    # TODO: Implement GitHub OAuth redirect
    return {"message": "GitHub OAuth redirect - not implemented in MVP"}


@router.get("/auth/callback/github")
async def oauth_github_callback(code: str, state: str | None = None):
    """Handle GitHub OAuth callback"""
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth not configured",
        )
    
    # TODO: Implement GitHub OAuth callback
    return {"message": "GitHub OAuth callback - not implemented in MVP"}


# =============================================================================
# Admin Routes (Protected)
# =============================================================================

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user by ID (admin only or self)"""
    # Allow users to view their own profile or admins to view any
    if str(current_user.id) != str(user_id) and "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)

