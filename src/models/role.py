"""Role and related models for RBAC."""

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class Role(Base):
    """Model for user roles with associated permissions."""

    __tablename__ = "roles"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    edit_mode_enabled = Column(Boolean, default=False)  # Per-role edit permission
    is_system_role = Column(Boolean, default=False)  # Built-in vs user-created
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin"
    )
    operations = relationship(
        "RoleOperation",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Role(name='{self.name}', edit_mode={self.edit_mode_enabled})>"

    def to_dict(self, include_operations: bool = True, include_users: bool = False) -> dict:
        """Convert role to dictionary.

        Args:
            include_operations: Whether to include operation list
            include_users: Whether to include assigned users

        Returns:
            Dictionary representation of role
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "edit_mode_enabled": self.edit_mode_enabled,
            "is_system_role": self.is_system_role,
            "operations_count": len(self.operations) if self.operations else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_operations and self.operations:
            data["operations"] = [op.operation_name for op in self.operations]
        if include_users and self.users:
            data["users"] = [{"id": u.id, "username": u.username} for u in self.users]
        return data

    def get_operation_names(self) -> List[str]:
        """Get list of operation names for this role.

        Returns:
            List of operation name strings
        """
        return [op.operation_name for op in self.operations] if self.operations else []


class RoleOperation(Base):
    """Model for mapping roles to allowed operations."""

    __tablename__ = "role_operations"

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_name = Column(String(255), nullable=False, index=True)  # e.g., "manage_createVlan"
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="operations")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("role_id", "operation_name", name="uq_role_operation"),
    )

    def __repr__(self) -> str:
        return f"<RoleOperation(role_id={self.role_id}, operation='{self.operation_name}')>"

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "role_id": self.role_id,
            "operation_name": self.operation_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserRole(Base):
    """Association table for users and roles (M:M relationship)."""

    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
