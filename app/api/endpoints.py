"""API endpoints for blog posts."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    BlogPost,
    BlogPostCreate,
    BlogPostRead,
    BlogPostUpdate,
    PaginationResponse,
    Tag,
)

router = APIRouter(prefix="/posts", tags=["posts"])


# ============================================================================
# POST /posts - Create Blog Post
# ============================================================================


@router.post("", response_model=BlogPostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: BlogPostCreate,
    session: Session = Depends(get_session),
) -> BlogPostRead:
    """Create a new blog post."""
    # Create or get tags
    tags = []
    for tag_name in post.tags:
        # Query for existing tag
        statement = select(Tag).where(Tag.name == tag_name)
        existing_tag = session.exec(statement).first()

        if existing_tag:
            tags.append(existing_tag)
        else:
            # Create new tag
            new_tag = Tag(name=tag_name)
            session.add(new_tag)
            session.flush()  # Flush to get the ID
            tags.append(new_tag)

    # Create blog post
    db_post = BlogPost(title=post.title, content=post.content, tags=tags)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)

    return db_post


# ============================================================================
# GET /posts/{id} - Read Blog Post
# ============================================================================


@router.get("/{post_id}", response_model=BlogPostRead)
async def get_post(
    post_id: int,
    session: Session = Depends(get_session),
) -> BlogPostRead:
    """Get a blog post by ID."""
    post = session.get(BlogPost, post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    return post


# ============================================================================
# GET /posts - List Blog Posts with Pagination and Filtering
# ============================================================================


@router.get("", response_model=PaginationResponse)
async def list_posts(
    cursor: Optional[int] = None,
    limit: int = 20,
    tag: Optional[str] = None,
    session: Session = Depends(get_session),
) -> PaginationResponse:
    """List blog posts with cursor-based pagination and optional tag filtering."""
    # Validate limit
    if limit < 1 or limit > 100:
        limit = 20

    # Query all posts with tags
    statement = select(BlogPost).order_by(BlogPost.id)
    all_posts = session.exec(statement).all()

    # Filter by tag if provided (eager load + Python filter)
    if tag:
        filtered_posts = [p for p in all_posts if any(t.name == tag for t in p.tags)]
    else:
        filtered_posts = all_posts

    # Apply cursor pagination
    start_idx = 0
    if cursor is not None:
        # Find posts after cursor
        for i, post in enumerate(filtered_posts):
            if post.id > cursor:
                start_idx = i
                break
        else:
            # Cursor is at or past the end
            start_idx = len(filtered_posts)

    # Get page items
    page_items = filtered_posts[start_idx : start_idx + limit]

    # Determine if there are more items
    has_more = start_idx + limit < len(filtered_posts)

    # Calculate next cursor
    next_cursor = None
    if page_items and has_more:
        next_cursor = page_items[-1].id

    return PaginationResponse(items=page_items, next_cursor=next_cursor, has_more=has_more)


# ============================================================================
# PATCH /posts/{id} - Update Blog Post
# ============================================================================


@router.patch("/{post_id}", response_model=BlogPostRead)
async def update_post(
    post_id: int,
    post_update: BlogPostUpdate,
    session: Session = Depends(get_session),
) -> BlogPostRead:
    """Update a blog post."""
    db_post = session.get(BlogPost, post_id)

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # Update fields if provided
    if post_update.title is not None:
        db_post.title = post_update.title

    if post_update.content is not None:
        db_post.content = post_update.content

    if post_update.tags is not None:
        # Handle tag updates
        tags = []
        for tag_name in post_update.tags:
            statement = select(Tag).where(Tag.name == tag_name)
            existing_tag = session.exec(statement).first()

            if existing_tag:
                tags.append(existing_tag)
            else:
                new_tag = Tag(name=tag_name)
                session.add(new_tag)
                session.flush()
                tags.append(new_tag)

        db_post.tags = tags

    # Update timestamp
    db_post.updated_at = datetime.utcnow()

    session.add(db_post)
    session.commit()
    session.refresh(db_post)

    return db_post


# ============================================================================
# DELETE /posts/{id} - Delete Blog Post
# ============================================================================


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    session: Session = Depends(get_session),
) -> None:
    """Delete a blog post."""
    post = session.get(BlogPost, post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    session.delete(post)
    session.commit()
