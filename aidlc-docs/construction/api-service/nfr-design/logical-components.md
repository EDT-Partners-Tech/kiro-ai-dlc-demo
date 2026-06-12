# Logical Components - API Service

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       HTTP Client                            │
└────────────────────────┬──────────────────────────────────────┘
                         │ HTTP Requests/Responses
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Global Exception Handler                         │   │
│  │     - Catches unhandled exceptions                  │   │
│  │     - Returns 500 errors                            │   │
│  │     - Logs error details                            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  2. Request Logging Middleware                       │   │
│  │     - Logs method, path, status code                │   │
│  │     - Adds timestamp                                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  3. HTTP Security Headers Middleware                │   │
│  │     - Adds CSP, HSTS, X-Frame-Options headers       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Route Handlers / API Endpoints                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. POST /posts                                       │  │
│  │     - Pydantic validation (BlogPostCreate)           │  │
│  │     - Create new BlogPost                            │  │
│  │     - Return 201 with created post                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  5. GET /posts/{id}                                  │  │
│  │     - Pydantic validation (path parameter)           │  │
│  │     - Query post by ID with tags                     │  │
│  │     - Return 200 or 404                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  6. GET /posts                                        │  │
│  │     - Pydantic validation (query params)             │  │
│  │     - Load all posts with tags (eager loading)       │  │
│  │     - Filter by tag if provided                      │  │
│  │     - Apply cursor-based pagination                  │  │
│  │     - Return 200 with paginated results              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  7. PATCH /posts/{id}                                │  │
│  │     - Pydantic validation (path + body)              │  │
│  │     - Query existing post                            │  │
│  │     - Update fields, set updated_at                  │  │
│  │     - Return 200 or 404                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  8. DELETE /posts/{id}                               │  │
│  │     - Pydantic validation (path parameter)           │  │
│  │     - Query post, delete from database               │  │
│  │     - Return 204 or 404                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Models (Pydantic + ORM)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  9. BlogPost (SQLModel)                              │  │
│  │     - id: int (auto-generated, primary key)          │  │
│  │     - title: str (required, < 500 chars)             │  │
│  │     - content: str (required, < 10000 chars)         │  │
│  │     - tags: list[Tag] (relationship, many-to-many)  │  │
│  │     - created_at: datetime (auto-generated)          │  │
│  │     - updated_at: datetime (auto-generated)          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  10. Tag (SQLModel)                                  │  │
│  │      - id: int (auto-generated, primary key)         │  │
│  │      - name: str (required, < 50 chars, unique)      │  │
│  │      - posts: list[BlogPost] (relationship)          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  11. PaginationResponse (Pydantic)                   │  │
│  │      - items: list[BlogPost]                         │  │
│  │      - next_cursor: int | None                       │  │
│  │      - has_more: bool                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Database Layer (SQLModel + SQLAlchemy)          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  12. Database Connection                             │  │
│  │      - SQLite file: ./blog-posts.db                  │  │
│  │      - Single connection, no pooling                 │  │
│  │      - Connection string: sqlite:///./blog-posts.db  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  13. Database Tables                                 │  │
│  │      - blog_posts (id, title, content, created_at,   │  │
│  │                   updated_at)                         │  │
│  │      - tags (id, name)                               │  │
│  │      - post_tags (post_id, tag_id) [junction table]  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  14. Session Management                              │  │
│  │      - Dependency injection for session per request  │  │
│  │      - Auto-commit on successful operations          │  │
│  │      - Auto-rollback on errors                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Global Exception Handler
**Responsibility**: Catch unhandled exceptions and return 500 errors

**Implementation**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Interactions**:
- Receives exceptions from all route handlers
- Logs full exception details
- Returns generic 500 response to client

---

### 2. Request Logging Middleware
**Responsibility**: Log each API request with method, path, status code

**Implementation**:
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response
```

**Interactions**:
- Intercepts all requests before routing
- Logs after response generated
- Adds timestamp automatically via logging framework

---

### 3. HTTP Security Headers Middleware
**Responsibility**: Add security headers to all responses

**Implementation**:
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

**Interactions**:
- Applied to all responses
- No conditional logic
- Protects against common web attacks

---

### 4-8. Route Handlers
**Responsibility**: Handle HTTP requests, validate input, orchestrate database operations

**Implementation Pattern**:
```python
@app.post("/posts", status_code=201)
async def create_post(post: BlogPostCreate, session: Session = Depends(get_session)):
    # Pydantic validation happens automatically
    db_post = BlogPost.from_orm(post)
    session.add(db_post)
    session.commit()
    return db_post

@app.get("/posts/{id}")
async def get_post(id: int, session: Session = Depends(get_session)):
    post = session.query(BlogPost).filter(BlogPost.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Similar for list, update, delete...
```

**Interactions**:
- Receive requests with validated input
- Use dependency injection for database session
- Interact with data models for ORM operations
- Return responses or raise HTTPException

---

### 9-11. Data Models
**Responsibility**: Define request/response schemas and database ORM models

**Implementation**:
```python
class BlogPost(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    content: str = Field(max_length=10000)
    tags: list["Tag"] = Relationship(back_populates="posts")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BlogPostCreate(SQLModel):
    title: str = Field(max_length=500)
    content: str = Field(max_length=10000)
    tags: list[str] = []
```

**Interactions**:
- Pydantic uses models for request/response validation
- SQLModel uses models for database ORM
- SQLAlchemy uses models for table schema
- Relationship tracking for tags

---

### 12-14. Database Layer
**Responsibility**: Manage database connections, tables, and sessions

**Implementation**:
```python
# Connection
DATABASE_URL = "sqlite:///./blog-posts.db"
engine = create_engine(DATABASE_URL, echo=False)

# Tables created on startup
SQLModel.metadata.create_all(engine)

# Session per request
def get_session():
    with Session(engine) as session:
        yield session
```

**Interactions**:
- Receives queries from route handlers
- Executes parameterized queries via SQLAlchemy
- Returns model instances
- Handles commit/rollback automatically

---

## Data Flow Example: Create Post

```
1. Client sends POST /posts with JSON body:
   {"title": "My Post", "content": "Content...", "tags": ["python"]}

2. Request Logging Middleware logs: "POST /posts -> ..."

3. Security Headers Middleware adds headers to response

4. Route handler POST /posts receives request

5. Pydantic validates input against BlogPostCreate model

6. Route handler creates BlogPost instance

7. Session adds new post to database

8. SQLAlchemy generates parameterized INSERT query

9. SQLite database executes query, assigns auto ID, timestamps

10. Session commits transaction

11. Route handler returns BlogPost instance

12. FastAPI serializes BlogPost to JSON

13. Response sent with 201 status code

14. Request Logging Middleware logs: "POST /posts -> 201"

15. Client receives response
```

---

## Error Flow Example: Get Non-Existent Post

```
1. Client sends GET /posts/999 (post doesn't exist)

2. Request Logging Middleware logs: "GET /posts/999 -> ..."

3. Route handler GET /posts/{id} receives request

4. Pydantic validates path parameter (id=999)

5. Route handler queries database: SELECT * FROM blog_posts WHERE id = 999

6. Query returns None (no post found)

7. Route handler raises HTTPException(status_code=404, detail="Post not found")

8. FastAPI catches HTTPException

9. Response generated with 404 status and JSON body: {"detail": "Post not found"}

10. Security headers added

11. Response sent with 404 status code

12. Request Logging Middleware logs: "GET /posts/999 -> 404"

13. Client receives 404 error response
```

---

## Component Interaction Summary

| Component | Calls | Called By | Purpose |
|-----------|-------|-----------|---------|
| Global Exception Handler | Logger | FastAPI | Catch all unhandled errors |
| Logging Middleware | Logger | FastAPI | Log request/response |
| Security Headers Middleware | (response) | FastAPI | Add security headers |
| Route Handlers | Session, Models | FastAPI | Handle API requests |
| Data Models | Pydantic, SQLAlchemy | Handlers, ORM | Define schemas and tables |
| Database Layer | SQLite | Data Models | Store/retrieve data |

All components work together to provide a simple, secure, and functional REST API with minimal complexity.
