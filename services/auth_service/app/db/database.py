"""
Idea Inc - Auth Service Database

PostgreSQL database connection and session management using SQLAlchemy async.
"""

import sys
import ssl
from pathlib import Path
from typing import AsyncGenerator

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

import certifi
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from shared.utils.config import get_settings
from shared.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    pass


# Create async engine
connect_args = {}
if settings.postgres_use_ssl:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.postgres_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables"""
    from app.db.models import User  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

