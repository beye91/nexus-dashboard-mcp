"""API endpoint model for tracking available operations."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from src.config.database import Base


class APIEndpoint(Base):
    """Model for API endpoint registry."""

    __tablename__ = "api_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String(50), nullable=False, index=True)
    operation_id = Column(String(255), nullable=False)
    http_method = Column(String(10), nullable=False)
    path = Column(String(512), nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    requires_edit_mode = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<APIEndpoint({self.http_method} {self.path}, operation_id='{self.operation_id}')>"

    def to_dict(self) -> dict:
        """Convert API endpoint to dictionary.

        Returns:
            Dictionary representation of API endpoint
        """
        return {
            "id": self.id,
            "api_name": self.api_name,
            "operation_id": self.operation_id,
            "http_method": self.http_method,
            "path": self.path,
            "enabled": self.enabled,
            "requires_edit_mode": self.requires_edit_mode,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_read_only(self) -> bool:
        """Check if this is a read-only operation.

        Returns:
            True if HTTP method is GET, False otherwise
        """
        return self.http_method.upper() == "GET"

    @property
    def is_write_operation(self) -> bool:
        """Check if this is a write operation.

        Returns:
            True if HTTP method is POST/PUT/DELETE/PATCH
        """
        return self.http_method.upper() in ["POST", "PUT", "DELETE", "PATCH"]
