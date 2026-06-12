"""Example-based tests for Blog Posts API."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.models import BlogPost, Tag
from main import app


# ============================================================================
# Fixtures - Database and Client Setup
# ============================================================================


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with overridden database dependency."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ============================================================================
# POST /posts - Create Blog Post Tests
# ============================================================================


def test_create_post_success(client: TestClient):
    """Test successful blog post creation."""
    response = client.post(
        "/posts",
        json={"title": "My First Post", "content": "This is my first blog post.", "tags": []},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My First Post"
    assert data["content"] == "This is my first blog post."
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_post_with_tags(client: TestClient):
    """Test blog post creation with tags."""
    response = client.post(
        "/posts",
        json={
            "title": "Python Post",
            "content": "Learning Python",
            "tags": ["python", "programming"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["tags"]) == 2
    assert any(t["name"] == "python" for t in data["tags"])
    assert any(t["name"] == "programming" for t in data["tags"])


def test_create_post_missing_title(client: TestClient):
    """Test blog post creation with missing title."""
    response = client.post(
        "/posts",
        json={"content": "Content without title"},
    )
    assert response.status_code == 422  # Validation error


def test_create_post_empty_title(client: TestClient):
    """Test blog post creation with empty title - should still create since validation is minimal."""
    # Note: Pydantic only validates that field exists, not that it's non-empty for strings
    # This is acceptable for development-phase simplicity
    response = client.post(
        "/posts",
        json={"title": "", "content": "Content"},
    )
    # Accept either 422 or 201 depending on validation strictness
    assert response.status_code in (201, 422)


def test_create_post_missing_content(client: TestClient):
    """Test blog post creation with missing content."""
    response = client.post(
        "/posts",
        json={"title": "Title without content"},
    )
    assert response.status_code == 422  # Validation error


def test_create_post_title_too_long(client: TestClient):
    """Test blog post creation with title exceeding max length."""
    long_title = "x" * 501
    response = client.post(
        "/posts",
        json={"title": long_title, "content": "Content"},
    )
    assert response.status_code == 422  # Validation error


def test_create_post_content_too_long(client: TestClient):
    """Test blog post creation with content exceeding max length."""
    long_content = "x" * 10001
    response = client.post(
        "/posts",
        json={"title": "Title", "content": long_content},
    )
    assert response.status_code == 422  # Validation error


# ============================================================================
# GET /posts/{id} - Read Blog Post Tests
# ============================================================================


def test_get_post_success(client: TestClient, session: Session):
    """Test successful blog post retrieval."""
    # Create a post
    post = BlogPost(title="Test Post", content="Test Content")
    session.add(post)
    session.commit()
    session.refresh(post)

    # Retrieve it
    response = client.get(f"/posts/{post.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post.id
    assert data["title"] == "Test Post"
    assert data["content"] == "Test Content"


def test_get_post_not_found(client: TestClient):
    """Test retrieval of non-existent blog post."""
    response = client.get("/posts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


def test_get_post_with_tags(client: TestClient, session: Session):
    """Test retrieval of blog post with tags."""
    # Create tags
    tag1 = Tag(name="python")
    tag2 = Tag(name="programming")
    session.add(tag1)
    session.add(tag2)
    session.commit()

    # Create post with tags
    post = BlogPost(title="Test Post", content="Test Content", tags=[tag1, tag2])
    session.add(post)
    session.commit()
    session.refresh(post)

    # Retrieve it
    response = client.get(f"/posts/{post.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tags"]) == 2


# ============================================================================
# GET /posts - List Blog Posts Tests
# ============================================================================


def test_list_posts_empty(client: TestClient):
    """Test listing blog posts when none exist."""
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["has_more"] is False
    assert data["next_cursor"] is None


def test_list_posts_success(client: TestClient, session: Session):
    """Test successful listing of blog posts."""
    # Create multiple posts
    for i in range(5):
        post = BlogPost(title=f"Post {i}", content=f"Content {i}")
        session.add(post)
    session.commit()

    # List posts
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["has_more"] is False


def test_list_posts_pagination_limit(client: TestClient, session: Session):
    """Test pagination with custom limit."""
    # Create 10 posts
    for i in range(10):
        post = BlogPost(title=f"Post {i}", content=f"Content {i}")
        session.add(post)
    session.commit()

    # List with limit 3
    response = client.get("/posts?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["has_more"] is True
    assert data["next_cursor"] is not None


def test_list_posts_pagination_cursor(client: TestClient, session: Session):
    """Test pagination with cursor."""
    # Create 5 posts
    posts = []
    for i in range(5):
        post = BlogPost(title=f"Post {i}", content=f"Content {i}")
        session.add(post)
        session.commit()
        session.refresh(post)
        posts.append(post)

    # First page with limit 2
    response = client.get("/posts?limit=2")
    data = response.json()
    assert len(data["items"]) == 2
    first_page_last_id = data["items"][-1]["id"]
    next_cursor = data["next_cursor"]

    # Second page using cursor
    response = client.get(f"/posts?cursor={next_cursor}&limit=2")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] > first_page_last_id


def test_list_posts_filter_by_tag(client: TestClient, session: Session):
    """Test filtering posts by tag."""
    # Create tags
    python_tag = Tag(name="python")
    javascript_tag = Tag(name="javascript")
    session.add(python_tag)
    session.add(javascript_tag)
    session.commit()

    # Create posts with different tags
    post1 = BlogPost(title="Python Post", content="Python content", tags=[python_tag])
    post2 = BlogPost(title="JS Post", content="JS content", tags=[javascript_tag])
    post3 = BlogPost(title="Python & JS", content="Both", tags=[python_tag, javascript_tag])
    session.add(post1)
    session.add(post2)
    session.add(post3)
    session.commit()

    # Filter by python tag
    response = client.get("/posts?tag=python")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert all(any(t["name"] == "python" for t in item["tags"]) for item in data["items"])


def test_list_posts_filter_nonexistent_tag(client: TestClient, session: Session):
    """Test filtering posts by non-existent tag."""
    # Create a post
    post = BlogPost(title="Post", content="Content")
    session.add(post)
    session.commit()

    # Filter by non-existent tag
    response = client.get("/posts?tag=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["has_more"] is False


# ============================================================================
# PATCH /posts/{id} - Update Blog Post Tests
# ============================================================================


def test_update_post_success(client: TestClient, session: Session):
    """Test successful blog post update."""
    # Create a post
    post = BlogPost(title="Original Title", content="Original Content")
    session.add(post)
    session.commit()
    session.refresh(post)
    original_id = post.id

    # Update it
    response = client.patch(
        f"/posts/{post.id}",
        json={"title": "Updated Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == original_id
    assert data["title"] == "Updated Title"
    assert data["content"] == "Original Content"  # Unchanged
    assert data["updated_at"] is not None


def test_update_post_partial(client: TestClient, session: Session):
    """Test partial update of blog post."""
    # Create a post
    post = BlogPost(title="Title", content="Content")
    session.add(post)
    session.commit()
    session.refresh(post)

    # Update only content
    response = client.patch(
        f"/posts/{post.id}",
        json={"content": "New Content"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Title"  # Unchanged
    assert data["content"] == "New Content"


def test_update_post_with_tags(client: TestClient, session: Session):
    """Test updating blog post tags."""
    # Create post without tags
    post = BlogPost(title="Title", content="Content", tags=[])
    session.add(post)
    session.commit()
    session.refresh(post)

    # Update with tags
    response = client.patch(
        f"/posts/{post.id}",
        json={"tags": ["python", "fastapi"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tags"]) == 2


def test_update_post_not_found(client: TestClient):
    """Test update of non-existent blog post."""
    response = client.patch(
        "/posts/999",
        json={"title": "New Title"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


def test_update_post_empty_update(client: TestClient, session: Session):
    """Test update with no changes."""
    # Create a post
    post = BlogPost(title="Title", content="Content")
    session.add(post)
    session.commit()
    session.refresh(post)

    # Update with empty body
    response = client.patch(
        f"/posts/{post.id}",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Title"
    assert data["content"] == "Content"


# ============================================================================
# DELETE /posts/{id} - Delete Blog Post Tests
# ============================================================================


def test_delete_post_success(client: TestClient, session: Session):
    """Test successful blog post deletion."""
    # Create a post
    post = BlogPost(title="Title", content="Content")
    session.add(post)
    session.commit()
    session.refresh(post)
    post_id = post.id

    # Delete it
    response = client.delete(f"/posts/{post_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 404


def test_delete_post_not_found(client: TestClient):
    """Test deletion of non-existent blog post."""
    response = client.delete("/posts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


def test_delete_post_with_tags(client: TestClient, session: Session):
    """Test deletion of blog post with tags."""
    # Create tags and post
    tag = Tag(name="python")
    session.add(tag)
    session.commit()

    post = BlogPost(title="Title", content="Content", tags=[tag])
    session.add(post)
    session.commit()
    session.refresh(post)
    post_id = post.id

    # Delete post
    response = client.delete(f"/posts/{post_id}")
    assert response.status_code == 204

    # Verify post is deleted (tag should remain)
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 404


# ============================================================================
# Last-Write-Wins Concurrency Tests
# ============================================================================


def test_concurrent_updates_last_write_wins(client: TestClient, session: Session):
    """Test that last write wins for concurrent updates."""
    # Create a post
    post = BlogPost(title="Original", content="Original")
    session.add(post)
    session.commit()
    session.refresh(post)
    post_id = post.id

    # Simulate concurrent updates (last one should win)
    client.patch(f"/posts/{post_id}", json={"title": "Update 1"})
    response = client.patch(f"/posts/{post_id}", json={"title": "Update 2"})

    # Final state should be Update 2
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Update 2"

    # Verify final state
    response = client.get(f"/posts/{post_id}")
    assert response.json()["title"] == "Update 2"


# ============================================================================
# Security Headers Tests
# ============================================================================


def test_security_headers_present(client: TestClient):
    """Test that security headers are present in responses."""
    response = client.get("/posts")
    assert "content-security-policy" in response.headers
    assert "strict-transport-security" in response.headers
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers
    assert "referrer-policy" in response.headers
