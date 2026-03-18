"""Tool profile models for controlling tool exposure to MCP clients."""

from typing import List, Optional, Set

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base


class ToolProfile(Base):
    """Model for tool profiles that control which tools are exposed to MCP clients.

    Tool profiles allow administrators to limit the number of operations visible
    to specific users, addressing MCP client tool limits (typically 40-128 tools)
    when the server exposes 600+ operations.

    Priority order for tool filtering:
    1. Tool profile (if assigned) - highest priority, even for superusers
    2. Superuser without profile - all tools
    3. Role-based operations - filtered by assigned role operations
    4. No roles and no profile - no tools
    """

    __tablename__ = "tool_profiles"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    max_tools = Column(Integer, default=100)  # 0 = no limit (Full Access profile)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    operations = relationship(
        "ToolProfileOperation",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ToolProfile(name='{self.name}', max_tools={self.max_tools})>"

    def to_dict(self, include_operations: bool = True) -> dict:
        """Convert tool profile to dictionary.

        Args:
            include_operations: Whether to include the list of operation names

        Returns:
            Dictionary representation of the tool profile
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "max_tools": self.max_tools,
            "is_active": self.is_active,
            "operations_count": len(self.operations) if self.operations else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_operations and self.operations:
            data["operations"] = [op.operation_name for op in self.operations]
        else:
            data["operations"] = []
        return data

    def get_operation_names(self) -> Set[str]:
        """Get set of operation names allowed by this profile.

        Returns:
            Set of operation name strings
        """
        return {op.operation_name for op in self.operations} if self.operations else set()


class ToolProfileOperation(Base):
    """Model for operations within a tool profile.

    Each row represents a single allowed operation name for the parent profile.
    The combination of (profile_id, operation_name) is unique.
    """

    __tablename__ = "tool_profile_operations"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(
        Integer,
        ForeignKey("tool_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_name = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    profile = relationship("ToolProfile", back_populates="operations")

    __table_args__ = (
        UniqueConstraint("profile_id", "operation_name", name="uq_profile_operation"),
    )

    def __repr__(self) -> str:
        return f"<ToolProfileOperation(profile_id={self.profile_id}, operation='{self.operation_name}')>"

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "operation_name": self.operation_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
