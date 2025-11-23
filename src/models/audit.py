"""Audit log model for tracking operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.config.database import Base


class AuditLog(Base):
    """Model for audit logging of all operations."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), index=True)
    user_id = Column(String(255))
    operation_id = Column(String(255), index=True)
    http_method = Column(String(10))
    path = Column(String(512))
    request_body = Column(JSONB)
    response_status = Column(Integer)
    response_body = Column(JSONB)
    error_message = Column(Text)
    client_ip = Column(String(45), index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog({self.http_method} {self.path}, status={self.response_status})>"

    def to_dict(self) -> dict:
        """Convert audit log entry to dictionary.

        Returns:
            Dictionary representation of audit log
        """
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "user_id": self.user_id,
            "operation_id": self.operation_id,
            "http_method": self.http_method,
            "path": self.path,
            "request_body": self.request_body,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "client_ip": self.client_ip,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @property
    def is_success(self) -> bool:
        """Check if the operation was successful.

        Returns:
            True if response status is 2xx, False otherwise
        """
        return self.response_status and 200 <= self.response_status < 300

    @property
    def is_error(self) -> bool:
        """Check if the operation resulted in an error.

        Returns:
            True if response status is 4xx or 5xx, or if error_message exists
        """
        return (
            self.error_message is not None
            or (self.response_status and self.response_status >= 400)
        )
