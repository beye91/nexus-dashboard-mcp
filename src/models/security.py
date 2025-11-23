"""Security configuration model."""

from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from src.config.database import Base


class SecurityConfig(Base):
    """Model for security configuration settings."""

    __tablename__ = "security_config"

    id = Column(Integer, primary_key=True, index=True)
    edit_mode_enabled = Column(Boolean, default=False, nullable=False)
    allowed_operations = Column(ARRAY(String), default=list)
    audit_logging = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SecurityConfig(edit_mode={self.edit_mode_enabled}, audit={self.audit_logging})>"

    def to_dict(self) -> dict:
        """Convert security config to dictionary.

        Returns:
            Dictionary representation of security configuration
        """
        return {
            "id": self.id,
            "edit_mode_enabled": self.edit_mode_enabled,
            "allowed_operations": self.allowed_operations or [],
            "audit_logging": self.audit_logging,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
