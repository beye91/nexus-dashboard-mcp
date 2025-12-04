"""User-Cluster association model for cluster access control."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func

from src.config.database import Base


class UserCluster(Base):
    """Association table for user-to-cluster access mapping.

    This M:M relationship controls which clusters a user can access.
    - If a user has no entries in this table and is a superuser, they can access all clusters.
    - If a user has no entries and is not a superuser, behavior depends on configuration.
    - If a user has entries, they can only access the specified clusters.
    """

    __tablename__ = "user_clusters"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    cluster_id = Column(
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<UserCluster(user_id={self.user_id}, cluster_id={self.cluster_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "cluster_id": self.cluster_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
