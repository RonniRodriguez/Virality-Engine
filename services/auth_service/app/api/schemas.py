"""
Idea Inc - Auth Service API Schemas

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# =============================================================================
# Request Schemas
# =============================================================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ProfileUpdate(BaseModel):
    """Profile update request"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)


# =============================================================================
# Response Schemas
# =============================================================================

class UserResponse(BaseModel):
    """User response (public info)"""
    id: UUID
    email: str
    display_name: Optional[str]
    roles: List[str]
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Public user info (for other users)"""
    id: UUID
    display_name: Optional[str]
    avatar_url: Optional[str]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# =============================================================================
# OAuth Schemas
# =============================================================================

class OAuthCallbackData(BaseModel):
    """OAuth callback data"""
    code: str
    state: Optional[str] = None


class OAuthUserInfo(BaseModel):
    """OAuth user info from provider"""
    provider: str
    provider_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

