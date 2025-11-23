"""Database configuration and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .settings import get_settings

# Base class for SQLAlchemy models
Base = declarative_base()


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str):
        """Initialize database connection.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url

        # Convert postgresql:// to postgresql+asyncpg:// for async support
        if database_url.startswith("postgresql://"):
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        else:
            async_url = database_url

        # Create async engine
        self.async_engine = create_async_engine(
            async_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )

        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create sync engine for migrations
        self.sync_engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )

        # Create sync session factory
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine,
            expire_on_commit=False,
        )

    async def create_tables(self):
        """Create all database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all database tables (use with caution)."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session.

        Yields:
            AsyncSession instance
        """
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close database connections."""
        await self.async_engine.dispose()
        self.sync_engine.dispose()


# Global database instance
_db_instance: Database = None


def get_db() -> Database:
    """Get or create database instance.

    Returns:
        Database instance
    """
    global _db_instance

    if _db_instance is None:
        settings = get_settings()
        _db_instance = Database(settings.database_url)

    return _db_instance


async def init_db():
    """Initialize database and create tables."""
    db = get_db()
    await db.create_tables()
