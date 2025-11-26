"""
Idea Inc - Security Utilities

JWT token management, password hashing, and security helpers.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from .config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data (should include 'sub' for user ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT string
    """
    settings = get_settings()
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),  # Unique token ID for revocation
        "type": "access",
    })
    
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Payload data (should include 'sub' for user ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT string
    """
    settings = get_settings()
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),
        "type": "refresh",
    })
    
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_token_pair(user_id: str, email: str, roles: list[str]) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User's unique identifier
        email: User's email
        roles: User's roles
        
    Returns:
        Dictionary with access_token, refresh_token, token_type, and expires_in
    """
    settings = get_settings()
    
    token_data = {
        "sub": user_id,
        "email": email,
        "roles": roles,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


def decode_token_unverified(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a token without verification (for debugging/logging).
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload without verification
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.InvalidTokenError:
        return None

