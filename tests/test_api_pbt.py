"""Property-based tests for Blog Posts API."""

from datetime import datetime

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from app.models import BlogPost, BlogPostCreate, BlogPostRead, Tag, TagRead, PaginationResponse


# ============================================================================
# Helper Strategies (defined first for use in other strategies)
# ============================================================================


@st.composite
def tag_read_strategy(draw):
    """Generate valid TagRead instances."""
    name = draw(st.text(min_size=1, max_size=50))
    return TagRead(id=draw(st.integers(min_value=1)), name=name)


@st.composite
def blog_post_read_strategy(draw):
    """Generate valid BlogPostRead instances."""
    title = draw(st.text(min_size=1, max_size=500))
    content = draw(st.text(min_size=1, max_size=10000))
    tags = draw(st.lists(tag_read_strategy(), max_size=10))
    return BlogPostRead(
        id=draw(st.integers(min_value=1)), title=title, content=content, tags=tags
    )


# ============================================================================
# Hypothesis Strategies for Domain Types
# ============================================================================


@st.composite
def blog_post_strategy(draw):
    """Generate valid BlogPost instances."""
    title = draw(st.text(min_size=1, max_size=500))
    content = draw(st.text(min_size=1, max_size=10000))
    return BlogPost(title=title, content=content)


@st.composite
def blog_post_create_strategy(draw):
    """Generate valid BlogPostCreate instances."""
    title = draw(st.text(min_size=1, max_size=500))
    content = draw(st.text(min_size=1, max_size=10000))
    tags = draw(st.lists(st.text(min_size=1, max_size=50), max_size=10))
    return BlogPostCreate(title=title, content=content, tags=tags)


@st.composite
def tag_strategy(draw):
    """Generate valid Tag instances."""
    name = draw(st.text(min_size=1, max_size=50))
    return Tag(name=name)


# ============================================================================
# Round-Trip Property Tests (PBT-02)
# ============================================================================


@given(blog_post_strategy())
def test_blog_post_dict_round_trip(blog_post):
    """BlogPost should serialize and deserialize to equivalent instance."""
    # Serialize to dict
    post_dict = blog_post.dict(exclude_unset=True)

    # Deserialize back
    restored = BlogPost(**post_dict)

    # Verify fields match (excluding auto-generated fields)
    assert restored.title == blog_post.title
    assert restored.content == blog_post.content


@given(tag_strategy())
def test_tag_dict_round_trip(tag):
    """Tag should serialize and deserialize to equivalent instance."""
    # Serialize to dict
    tag_dict = tag.dict(exclude_unset=True)

    # Deserialize back
    restored = Tag(**tag_dict)

    # Verify fields match
    assert restored.name == tag.name


@given(blog_post_create_strategy())
def test_blog_post_create_validation(post_create):
    """BlogPostCreate should validate correctly through serialization."""
    # Convert to dict
    post_dict = post_create.dict()

    # Deserialize and re-validate
    validated = BlogPostCreate(**post_dict)

    # Should match original
    assert validated.title == post_create.title
    assert validated.content == post_create.content
    assert validated.tags == post_create.tags


# ============================================================================
# Invariant Property Tests (PBT-03)
# ============================================================================


@given(st.text(min_size=1, max_size=500))
def test_blog_post_title_length_invariant(title):
    """BlogPost title should never exceed max length."""
    blog_post = BlogPost(title=title, content="content")
    assert len(blog_post.title) <= 500


@given(st.text(min_size=1, max_size=10000))
def test_blog_post_content_length_invariant(content):
    """BlogPost content should never exceed max length."""
    blog_post = BlogPost(title="title", content=content)
    assert len(blog_post.content) <= 10000


@given(st.lists(st.text(min_size=1, max_size=50), max_size=10))
def test_tag_list_length_invariant(tags):
    """Tag list should not exceed max size."""
    blog_post = BlogPostCreate(title="title", content="content", tags=tags)
    assert len(blog_post.tags) <= 10


@given(st.lists(st.text(min_size=1, max_size=50), max_size=10))
def test_individual_tag_length_invariant(tags):
    """Each individual tag should not exceed max length."""
    blog_post = BlogPostCreate(title="title", content="content", tags=tags)
    for tag in blog_post.tags:
        assert len(tag) <= 50


# ============================================================================
# Pagination Response Invariant Tests
# ============================================================================


@given(st.lists(st.integers(min_value=1), max_size=20))
def test_pagination_response_items_count(item_ids):
    """Pagination response should preserve item count."""
    items = [
        BlogPostRead(
            id=item_id,
            title=f"Post {item_id}",
            content="Content",
            tags=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for item_id in item_ids
    ]
    response = PaginationResponse(
        items=items, next_cursor=None if not items else items[-1].id + 1, has_more=False
    )
    assert len(response.items) == len(items)


@given(
    st.lists(st.integers(min_value=1), min_size=1, max_size=20),
    st.integers(min_value=1, max_value=100),
)
def test_pagination_has_more_invariant(item_ids, next_cursor):
    """Pagination has_more should be True if next_cursor is set."""
    items = [
        BlogPostRead(
            id=item_id,
            title=f"Post {item_id}",
            content="Content",
            tags=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for item_id in item_ids
    ]
    if next_cursor is not None:
        response = PaginationResponse(items=items, next_cursor=next_cursor, has_more=True)
        assert response.has_more is True


# ============================================================================
# Helper Strategy (no longer needed at end)
# ============================================================================
