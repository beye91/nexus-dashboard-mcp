"""User and UserSession models for authentication."""

from datetime import datetime
from typing import List, Optional, Set, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.role import Role
    from src.models.cluster import Cluster


class User(Base):
    """Model for user accounts with authentication."""

    __tablename__ = "users"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    email = Column(String(255), index=True)
    display_name = Column(String(255))
    api_token = Column(String(64), unique=True, index=True)  # For Claude Desktop auth
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    auth_type = Column(String(50), default="local")  # 'local' or 'ldap'
    ldap_dn = Column(String(500))  # Distinguished Name for LDAP users
    ldap_config_id = Column(Integer, ForeignKey("ldap_config.id", ondelete="SET NULL"))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    clusters = relationship(
        "Cluster",
        secondary="user_clusters",
        back_populates="users",
        lazy="selectin"
    )
    ldap_config = relationship("LDAPConfig", foreign_keys=[ldap_config_id])

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', active={self.is_active})>"

    def to_dict(self, include_roles: bool = True, include_clusters: bool = True) -> dict:
        """Convert user to dictionary (excluding sensitive data).

        Args:
            include_roles: Whether to include role details
            include_clusters: Whether to include cluster details

        Returns:
            Dictionary representation of user
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "auth_type": self.auth_type,
            "ldap_dn": self.ldap_dn if self.auth_type == "ldap" else None,
            "has_edit_mode": self.has_edit_mode(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_roles and self.roles:
            data["roles"] = [role.to_dict(include_operations=False) for role in self.roles]
        else:
            data["roles"] = []
        if include_clusters and self.clusters:
            data["clusters"] = [{"id": c.id, "name": c.name} for c in self.clusters]
        else:
            data["clusters"] = []
        return data

    def get_all_operations(self) -> set:
        """Get all allowed operations from all assigned roles.

        Returns:
            Set of operation names the user is allowed to perform
        """
        operations = set()
        for role in self.roles:
            for role_op in role.operations:
                operations.add(role_op.operation_name)
        return operations

    def has_edit_mode(self) -> bool:
        """Check if user has edit mode enabled through any role.

        Returns:
            True if any assigned role has edit_mode_enabled
        """
        if self.is_superuser:
            return True
        return any(role.edit_mode_enabled for role in self.roles)

    def can_perform_operation(self, operation_name: str) -> bool:
        """Check if user can perform a specific operation.

        Args:
            operation_name: Name of the operation to check

        Returns:
            True if user is allowed to perform the operation
        """
        if self.is_superuser:
            return True
        return operation_name in self.get_all_operations()

    def get_allowed_cluster_ids(self) -> Set[int]:
        """Get set of cluster IDs this user can access.

        Returns:
            Set of cluster IDs. Empty set means:
            - For superusers: access to all clusters
            - For regular users: depends on configuration
        """
        return {c.id for c in self.clusters} if self.clusters else set()

    def can_access_cluster(self, cluster_id: int) -> bool:
        """Check if user can access a specific cluster.

        Args:
            cluster_id: ID of the cluster to check

        Returns:
            True if user can access the cluster
        """
        if self.is_superuser:
            return True
        allowed = self.get_allowed_cluster_ids()
        if not allowed:
            # No clusters assigned - depends on policy
            # For now, deny access if no clusters assigned
            return False
        return cluster_id in allowed


class UserSession(Base):
    """Model for user authentication sessions."""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(user_id={self.user_id}, expires_at={self.expires_at})>"

    def is_expired(self) -> bool:
        """Check if session has expired.

        Returns:
            True if session is expired
        """
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict:
        """Convert session to dictionary.

        Returns:
            Dictionary representation of session
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
