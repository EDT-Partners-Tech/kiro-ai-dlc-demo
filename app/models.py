"""Data models for Blog Posts API."""

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


# Junction table for many-to-many relationship
class PostTag(SQLModel, table=True):
    """Junction table for blog post and tag relationship."""

    post_id: Optional[int] = Field(default=None, foreign_key="blogpost.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class TagBase(SQLModel):
    """Base tag model."""

    name: str = Field(max_length=50, index=True)


class Tag(TagBase, table=True):
    """Tag database model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    posts: list["BlogPost"] = Relationship(
        back_populates="tags",
        link_model=PostTag,
    )


class TagRead(TagBase):
    """Tag read schema."""

    id: int


class BlogPostBase(SQLModel):
    """Base blog post model."""

    title: str = Field(max_length=500)
    content: str = Field(max_length=10000)


class BlogPostCreate(BlogPostBase):
    """Blog post creation request model."""

    tags: list[str] = Field(default=[])


class BlogPostUpdate(SQLModel):
    """Blog post update request model."""

    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = Field(default=None, max_length=10000)
    tags: Optional[list[str]] = Field(default=None)


class BlogPost(BlogPostBase, table=True):
    """Blog post database model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    tags: list[Tag] = Relationship(
        back_populates="posts",
        link_model=PostTag,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BlogPostRead(BlogPostBase):
    """Blog post read schema."""

    id: int
    tags: list[TagRead] = []
    created_at: datetime
    updated_at: datetime


class PaginationResponse(SQLModel):
    """Pagination response model."""

    items: list[BlogPostRead]
    next_cursor: Optional[int] = None
    has_more: bool
