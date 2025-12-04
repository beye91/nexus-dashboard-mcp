"""LDAP configuration models for optional LDAP authentication."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.role import Role
    from src.models.cluster import Cluster


class LDAPConfig(Base):
    """Model for LDAP server configuration.

    Supports both Microsoft Active Directory and OpenLDAP/FreeIPA
    with configurable attribute mapping.
    """

    __tablename__ = "ldap_config"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)

    # Connection Settings
    server_url = Column(String(500), nullable=False)  # ldap:// or ldaps://
    base_dn = Column(String(500), nullable=False)
    bind_dn = Column(String(500))  # Admin user for searches
    bind_password_encrypted = Column(Text)  # Encrypted with Fernet

    # TLS/SSL Settings
    use_ssl = Column(Boolean, default=False)
    use_starttls = Column(Boolean, default=False)
    verify_ssl = Column(Boolean, default=True)
    ca_certificate = Column(Text)

    # User Search Settings
    user_search_base = Column(String(500))
    user_search_filter = Column(String(500), default="(objectClass=person)")
    user_object_class = Column(String(100), default="person")

    # User Attribute Mapping
    username_attribute = Column(String(100), default="sAMAccountName")
    email_attribute = Column(String(100), default="mail")
    display_name_attribute = Column(String(100), default="displayName")
    member_of_attribute = Column(String(100), default="memberOf")

    # Group Search Settings
    group_search_base = Column(String(500))
    group_search_filter = Column(String(500), default="(objectClass=group)")
    group_object_class = Column(String(100), default="group")
    group_name_attribute = Column(String(100), default="cn")
    group_member_attribute = Column(String(100), default="member")

    # Sync Settings
    sync_interval_minutes = Column(Integer, default=60)
    auto_create_users = Column(Boolean, default=True)
    auto_sync_groups = Column(Boolean, default=True)
    default_role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"))

    # Status Tracking
    last_sync_at = Column(DateTime)
    last_sync_status = Column(String(50))  # 'success', 'partial', 'failed'
    last_sync_message = Column(Text)
    last_sync_users_created = Column(Integer, default=0)
    last_sync_users_updated = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    role_mappings = relationship(
        "LDAPGroupRoleMapping",
        back_populates="ldap_config",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    cluster_mappings = relationship(
        "LDAPGroupClusterMapping",
        back_populates="ldap_config",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    default_role = relationship("Role", foreign_keys=[default_role_id])

    def __repr__(self) -> str:
        return f"<LDAPConfig(name='{self.name}', enabled={self.is_enabled})>"

    def to_dict(self, include_mappings: bool = False) -> dict:
        """Convert to dictionary (excluding sensitive data like bind password)."""
        data = {
            "id": self.id,
            "name": self.name,
            "is_enabled": self.is_enabled,
            "is_primary": self.is_primary,
            "server_url": self.server_url,
            "base_dn": self.base_dn,
            "bind_dn": self.bind_dn,
            # Never include bind_password_encrypted
            "use_ssl": self.use_ssl,
            "use_starttls": self.use_starttls,
            "verify_ssl": self.verify_ssl,
            "has_ca_certificate": bool(self.ca_certificate),
            "user_search_base": self.user_search_base,
            "user_search_filter": self.user_search_filter,
            "user_object_class": self.user_object_class,
            "username_attribute": self.username_attribute,
            "email_attribute": self.email_attribute,
            "display_name_attribute": self.display_name_attribute,
            "member_of_attribute": self.member_of_attribute,
            "group_search_base": self.group_search_base,
            "group_search_filter": self.group_search_filter,
            "group_object_class": self.group_object_class,
            "group_name_attribute": self.group_name_attribute,
            "group_member_attribute": self.group_member_attribute,
            "sync_interval_minutes": self.sync_interval_minutes,
            "auto_create_users": self.auto_create_users,
            "auto_sync_groups": self.auto_sync_groups,
            "default_role_id": self.default_role_id,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_sync_status": self.last_sync_status,
            "last_sync_message": self.last_sync_message,
            "last_sync_users_created": self.last_sync_users_created,
            "last_sync_users_updated": self.last_sync_users_updated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_mappings:
            data["role_mappings"] = [m.to_dict() for m in self.role_mappings]
            data["cluster_mappings"] = [m.to_dict() for m in self.cluster_mappings]
        return data


class LDAPGroupRoleMapping(Base):
    """Map LDAP groups to roles for automatic role assignment."""

    __tablename__ = "ldap_group_role_mappings"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)
    ldap_config_id = Column(
        Integer,
        ForeignKey("ldap_config.id", ondelete="CASCADE"),
        nullable=False
    )
    ldap_group_dn = Column(String(500), nullable=False)
    ldap_group_name = Column(String(255), nullable=False)
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    ldap_config = relationship("LDAPConfig", back_populates="role_mappings")
    role = relationship("Role")

    def __repr__(self) -> str:
        return f"<LDAPGroupRoleMapping(group='{self.ldap_group_name}', role_id={self.role_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "ldap_config_id": self.ldap_config_id,
            "ldap_group_dn": self.ldap_group_dn,
            "ldap_group_name": self.ldap_group_name,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LDAPGroupClusterMapping(Base):
    """Map LDAP groups to clusters for automatic cluster access."""

    __tablename__ = "ldap_group_cluster_mappings"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)
    ldap_config_id = Column(
        Integer,
        ForeignKey("ldap_config.id", ondelete="CASCADE"),
        nullable=False
    )
    ldap_group_dn = Column(String(500), nullable=False)
    ldap_group_name = Column(String(255), nullable=False)
    cluster_id = Column(
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    ldap_config = relationship("LDAPConfig", back_populates="cluster_mappings")
    cluster = relationship("Cluster")

    def __repr__(self) -> str:
        return f"<LDAPGroupClusterMapping(group='{self.ldap_group_name}', cluster_id={self.cluster_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "ldap_config_id": self.ldap_config_id,
            "ldap_group_dn": self.ldap_group_dn,
            "ldap_group_name": self.ldap_group_name,
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster.name if self.cluster else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
