"""Resource group models for MCP tool consolidation."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base


class ResourceGroup(Base):
    """Model for resource groups (consolidated MCP tools).

    Resource groups allow customization of how API operations are grouped
    into MCP tools. By default, operations are grouped by resource type
    (first path segment), but users can create custom groups.
    """

    __tablename__ = "resource_groups"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    group_key = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "analyze_fabrics"
    display_name = Column(String(200))  # Human-readable name
    description = Column(Text)  # Description shown in MCP tool
    is_enabled = Column(Boolean, default=True)  # Enable/disable this group
    is_custom = Column(Boolean, default=False)  # True if user-created
    sort_order = Column(Integer, default=0)  # For UI ordering
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    mappings = relationship(
        "ResourceGroupMapping",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ResourceGroup(key='{self.group_key}', enabled={self.is_enabled})>"

    def to_dict(self, include_mappings: bool = True) -> dict:
        """Convert resource group to dictionary.

        Args:
            include_mappings: Whether to include operation mappings

        Returns:
            Dictionary representation of resource group
        """
        data = {
            "id": self.id,
            "group_key": self.group_key,
            "display_name": self.display_name,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "is_custom": self.is_custom,
            "sort_order": self.sort_order,
            "operations_count": len(self.mappings) if self.mappings else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_mappings and self.mappings:
            data["operations"] = [m.to_dict() for m in self.mappings]
        return data

    def get_operation_ids(self) -> List[str]:
        """Get list of operation IDs in this group.

        Returns:
            List of operation_id strings
        """
        return [m.operation_id for m in self.mappings] if self.mappings else []


class ResourceGroupMapping(Base):
    """Model for mapping operations to resource groups.

    Each operation can only belong to one group (enforced by unique constraint).
    """

    __tablename__ = "resource_group_mappings"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("resource_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_id = Column(String(255), nullable=False, index=True)  # The operation_id from api_endpoints
    api_name = Column(String(50), nullable=False)  # API name (analyze, infra, manage, onemanage)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    group = relationship("ResourceGroup", back_populates="mappings")

    # Unique constraint: each operation can only be in one group
    __table_args__ = (
        UniqueConstraint("operation_id", "api_name", name="uq_operation_api"),
    )

    def __repr__(self) -> str:
        return f"<ResourceGroupMapping(group_id={self.group_id}, operation='{self.operation_id}')>"

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "group_id": self.group_id,
            "operation_id": self.operation_id,
            "api_name": self.api_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
