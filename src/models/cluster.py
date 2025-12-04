"""Cluster model for storing Nexus Dashboard connection information."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class Cluster(Base):
    """Model for Nexus Dashboard cluster credentials."""

    __tablename__ = "clusters"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    url = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    verify_ssl = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship(
        "User",
        secondary="user_clusters",
        back_populates="clusters",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Cluster(name='{self.name}', url='{self.url}', active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert cluster to dictionary (excluding sensitive data).

        Returns:
            Dictionary representation of cluster
        """
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "username": self.username,
            "verify_ssl": self.verify_ssl,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
