"""Guidance system models for API assistance and workflows."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base

if TYPE_CHECKING:
    from typing import Any


class APIGuidance(Base):
    """Model for API-level guidance and recommendations."""

    __tablename__ = "api_guidance"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    when_to_use = Column(Text)
    when_not_to_use = Column(Text)
    examples = Column(JSONB, default=list)
    priority = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<APIGuidance(api_name='{self.api_name}', display_name='{self.display_name}')>"

    def to_dict(self) -> dict:
        """Convert API guidance to dictionary.

        Returns:
            Dictionary representation of API guidance
        """
        return {
            "id": self.id,
            "api_name": self.api_name,
            "display_name": self.display_name,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "when_not_to_use": self.when_not_to_use,
            "examples": self.examples if self.examples else [],
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CategoryGuidance(Base):
    """Model for category/tag-level guidance."""

    __tablename__ = "category_guidance"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String(50), nullable=False, index=True)
    category_name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    when_to_use = Column(Text)
    related_categories = Column(JSONB, default=list)
    priority = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("api_name", "category_name", name="uq_api_category"),
    )

    def __repr__(self) -> str:
        return f"<CategoryGuidance(api_name='{self.api_name}', category='{self.category_name}')>"

    def to_dict(self) -> dict:
        """Convert category guidance to dictionary.

        Returns:
            Dictionary representation of category guidance
        """
        return {
            "id": self.id,
            "api_name": self.api_name,
            "category_name": self.category_name,
            "display_name": self.display_name,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "related_categories": self.related_categories if self.related_categories else [],
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Workflow(Base):
    """Model for workflow definitions."""

    __tablename__ = "workflows"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    problem_statement = Column(Text)
    use_case_tags = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkflowStep.step_order"
    )

    def __repr__(self) -> str:
        return f"<Workflow(name='{self.name}', display_name='{self.display_name}')>"

    def to_dict(self, include_steps: bool = True) -> dict:
        """Convert workflow to dictionary.

        Args:
            include_steps: Whether to include workflow steps

        Returns:
            Dictionary representation of workflow
        """
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "problem_statement": self.problem_statement,
            "use_case_tags": self.use_case_tags if self.use_case_tags else [],
            "is_active": self.is_active,
            "priority": self.priority,
            "steps_count": len(self.steps) if self.steps else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_steps and self.steps:
            data["steps"] = [step.to_dict() for step in self.steps]
        return data


class WorkflowStep(Base):
    """Model for steps within workflows."""

    __tablename__ = "workflow_steps"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(
        Integer,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    step_order = Column(Integer, nullable=False, index=True)
    operation_name = Column(String(255), nullable=False)
    description = Column(Text)
    expected_output = Column(Text)
    optional = Column(Boolean, default=False)
    fallback_operation = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("workflow_id", "step_order", name="uq_workflow_step_order"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowStep(workflow_id={self.workflow_id}, order={self.step_order}, operation='{self.operation_name}')>"

    def to_dict(self) -> dict:
        """Convert workflow step to dictionary.

        Returns:
            Dictionary representation of workflow step
        """
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "step_order": self.step_order,
            "operation_name": self.operation_name,
            "description": self.description,
            "expected_output": self.expected_output,
            "optional": self.optional,
            "fallback_operation": self.fallback_operation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ToolDescriptionOverride(Base):
    """Model for enhanced tool descriptions and usage hints."""

    __tablename__ = "tool_description_overrides"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    operation_name = Column(String(255), unique=True, nullable=False, index=True)
    enhanced_description = Column(Text)
    usage_hint = Column(Text)
    related_tools = Column(JSONB, default=list)
    common_parameters = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ToolDescriptionOverride(operation_name='{self.operation_name}')>"

    def to_dict(self) -> dict:
        """Convert tool description override to dictionary.

        Returns:
            Dictionary representation of tool description override
        """
        return {
            "id": self.id,
            "operation_name": self.operation_name,
            "enhanced_description": self.enhanced_description,
            "usage_hint": self.usage_hint,
            "related_tools": self.related_tools if self.related_tools else [],
            "common_parameters": self.common_parameters if self.common_parameters else [],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SystemPromptSection(Base):
    """Model for system prompt sections."""

    __tablename__ = "system_prompt_sections"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    section_name = Column(String(100), unique=True, nullable=False, index=True)
    section_order = Column(Integer, default=0, index=True)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SystemPromptSection(section_name='{self.section_name}', order={self.section_order})>"

    def to_dict(self) -> dict:
        """Convert system prompt section to dictionary.

        Returns:
            Dictionary representation of system prompt section
        """
        return {
            "id": self.id,
            "section_name": self.section_name,
            "section_order": self.section_order,
            "title": self.title,
            "content": self.content,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
