"""
Data models for CloudSpend Analytics API.

Defines SQLModel tables and Pydantic schemas for:
- Cost entries (immutable cloud cost records)
- Tags (cost allocation tags)
- Recommendations (FinOps optimization opportunities)
- Audit logs (status change tracking)
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship
from pydantic import validator, field_validator


# ============================================================================
# Database Models (SQLModel - combines SQLAlchemy + Pydantic)
# ============================================================================


class CostEntryTag(SQLModel, table=True):
    """Many-to-many join table: CostEntry <-> Tag"""
    cost_entry_id: Optional[str] = Field(
        default=None,
        foreign_key="costentry.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    tag_id: Optional[str] = Field(
        default=None,
        foreign_key="tag.id",
        primary_key=True
    )


class Tag(SQLModel, table=True):
    """Cost allocation tag."""
    id: str = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: str
    
    # Relationships
    costs: List["CostEntry"] = Relationship(
        back_populates="tags",
        link_model=CostEntryTag
    )


class CostEntry(SQLModel, table=True):
    """Immutable cloud cost record."""
    id: str = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    amount: str  # Stored as TEXT for Decimal precision
    timestamp: str = Field(index=True)  # ISO 8601 UTC
    created_at: str
    updated_at: str
    
    # Relationships
    tags: List[Tag] = Relationship(
        back_populates="costs",
        link_model=CostEntryTag
    )


class Recommendation(SQLModel, table=True):
    """Cost optimization recommendation."""
    id: str = Field(default=None, primary_key=True)
    title: str
    description: str
    estimated_monthly_savings: str  # Stored as TEXT for Decimal precision
    service: str = Field(index=True)
    status: str = Field(default="recommended", index=True)  # recommended, implemented, dismissed
    created_at: str
    updated_at: str


class RecommendationStatusAudit(SQLModel, table=True):
    """Audit log for recommendation status changes."""
    id: str = Field(default=None, primary_key=True)
    recommendation_id: str = Field(foreign_key="recommendation.id")
    old_status: Optional[str] = None
    new_status: str
    timestamp: str


# ============================================================================
# Pydantic Request Schemas
# ============================================================================


class CostEntryRequest(SQLModel):
    """Request schema for creating a cost entry."""
    service: str
    amount: str
    timestamp: str
    tags: Optional[List[str]] = None
    
    @field_validator("service")
    @classmethod
    def validate_service(cls, v):
        """Service name must be alphanumeric + hyphens."""
        if not v or not all(c.isalnum() or c == '-' for c in v):
            raise ValueError("Service name must be alphanumeric or hyphens")
        if len(v) > 64:
            raise ValueError("Service name must be <= 64 characters")
        return v
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Amount must be positive decimal."""
        try:
            amount = Decimal(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if amount.as_tuple().exponent < -2:
                raise ValueError("Amount must have max 2 decimal places")
            return str(amount)
        except Exception as e:
            raise ValueError(f"Invalid amount: {e}")
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """Timestamp must be ISO 8601 UTC, not in future."""
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            if dt > now:
                raise ValueError("Timestamp cannot be in the future")
            return v
        except Exception as e:
            raise ValueError(f"Invalid timestamp: {e}")
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Tags must be non-empty strings."""
        if v:
            for tag in v:
                if not tag or not isinstance(tag, str):
                    raise ValueError("Tags must be non-empty strings")
                if len(tag) > 64:
                    raise ValueError("Tag must be <= 64 characters")
        return v or []


class RecommendationStatusUpdate(SQLModel):
    """Request schema for updating recommendation status."""
    status: str
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Status must be implemented or dismissed."""
        if v not in ("implemented", "dismissed"):
            raise ValueError(f"Status must be 'implemented' or 'dismissed', got '{v}'")
        return v


# ============================================================================
# Pydantic Response Schemas
# ============================================================================


class CostEntryResponse(SQLModel):
    """Response schema for cost entry."""
    id: str
    service: str
    amount: str
    timestamp: str
    tags: List[str] = []
    created_at: str
    updated_at: str


class DailyTrendResponse(SQLModel):
    """Response schema for daily spending aggregate."""
    date: str  # ISO 8601 date (YYYY-MM-DD)
    total_cost: str
    cost_count: int


class DailyTrendsListResponse(SQLModel):
    """Paginated response for daily trends."""
    items: List[DailyTrendResponse]
    next_cursor: Optional[str] = None
    has_more: bool
    items_count: int


class AnomalyResponse(SQLModel):
    """Response schema for detected anomaly."""
    date: str
    service: str
    baseline_average: str
    spike_cost: str
    spike_percentage: Decimal


class AnomaliesListResponse(SQLModel):
    """Response for anomalies list."""
    anomalies: List[AnomalyResponse]
    total_count: int


class RecommendationResponse(SQLModel):
    """Response schema for recommendation."""
    id: str
    title: str
    description: str
    estimated_monthly_savings: str
    service: str
    status: str
    created_at: str
    updated_at: str


class RecommendationsListResponse(SQLModel):
    """Paginated response for recommendations."""
    items: List[RecommendationResponse]
    next_cursor: Optional[str] = None
    has_more: bool
    items_count: int


class HealthResponse(SQLModel):
    """Response schema for health check."""
    status: str


class ApiInfoResponse(SQLModel):
    """Response schema for API info."""
    name: str
    version: str
    docs_url: str
