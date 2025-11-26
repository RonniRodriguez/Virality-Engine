"""
Idea Inc - Auth Service Database Models

SQLAlchemy models for user authentication and sessions.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    """User model for authentication"""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,  # Null for OAuth users
    )
    
    # OAuth provider info
    provider: Mapped[str] = mapped_column(
        String(50),
        default="local",
        nullable=False,
    )
    provider_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Roles and permissions
    roles: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        default=["player"],
        nullable=False,
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class RefreshToken(Base):
    """Refresh token storage for token rotation"""
    
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Device/session info
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"<RefreshToken {self.id}>"

