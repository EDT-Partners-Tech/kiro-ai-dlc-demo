# NFR Design Patterns - API Service

## Design Pattern Summary

Based on your selections for the simplest approach, the following patterns are incorporated into the API Service design:

---

## Security Patterns

### Input Validation Pattern: Request-Model-Only
**Pattern**: Single-layer validation at API request layer using Pydantic models

```
Client Request → Pydantic Validation → Route Handler
                      ↓
                  Reject if invalid
                  (400 Bad Request)
```

**Implementation**:
- All request bodies validated by Pydantic models before reaching handlers
- Type checking, required field validation, and field constraints enforced
- No additional validation layers needed
- Validation errors return clear 400 Bad Request with field details

**Models**:
```python
class BlogPostCreate(BaseModel):
    title: str  # Required, non-empty
    content: str  # Required, non-empty
    tags: list[str] = []  # Optional, list of strings

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None

class Tag(BaseModel):
    name: str  # Required, non-empty
```

**Benefits**: Simple, leverages FastAPI/Pydantic built-in validation, no redundant checks

---

### SQL Injection Prevention: ORM-Only
**Pattern**: Exclusive use of SQLModel ORM, no raw SQL queries

```
Request → Pydantic Model → SQLModel ORM → Parameterized Query → Database
                                ↓
                        All queries parameterized
                        No string concatenation
```

**Implementation**:
- All database operations use SQLModel ORM methods (session.query, session.add, etc.)
- No raw SQL strings in code
- SQLAlchemy handles parameterization automatically
- All user inputs passed as ORM parameters, never concatenated into queries

**Example**:
```python
# SAFE - Using ORM
posts = session.query(BlogPost).filter(BlogPost.id == post_id).first()

# NOT USED - Raw SQL would be unsafe without parameterization
# DO NOT: query = f"SELECT * FROM blog_posts WHERE id = {post_id}"
```

**Benefits**: Eliminates SQL injection risk entirely, cleaner code, type-safe

---

### Error Recovery: Fail-Fast Pattern
**Pattern**: Return immediate 500 error on database connection failure, no retry logic

```
Request → Database Operation
              ↓
         Connection Fails?
              ↓
         Return 500 Immediately
```

**Implementation**:
- No automatic retries on database failures
- Connection errors propagate immediately to error handler
- Client receives 500 Internal Server Error
- Application logs the error for debugging
- Developer restarts service if needed

**Benefits**: Simple, predictable behavior, no complex state tracking, easier debugging

---

### Error Response Format: Basic
**Pattern**: Simple error responses with status code and message only

```json
{
  "detail": "Not found"
}
```

**Implementation**:
- All error responses use `{"detail": "message"}` format
- No error codes or error types
- No field-level validation details
- Generic messages for production (no internal details)
- HTTP status codes carry the semantic meaning

**Examples**:
```json
// 400 Bad Request
{"detail": "title must be non-empty"}

// 404 Not Found
{"detail": "Post not found"}

// 500 Internal Server Error
{"detail": "Internal server error"}
```

**Benefits**: Minimal response payload, clear message, easy to parse

---

### Logging Pattern: Minimal
**Pattern**: Log only status code and path for each request

```
[2024-01-15 10:23:45] POST /posts -> 201
[2024-01-15 10:24:12] GET /posts/123 -> 200
[2024-01-15 10:25:03] PATCH /posts/999 -> 404
```

**Implementation**:
- Middleware logs each request with method, path, status code
- Timestamp added automatically
- No request/response body logging
- No client IP or detailed headers
- Error tracebacks logged only for 5xx errors

**Logging Library**: Python `logging` module with StreamHandler to stdout

**Benefits**: Simple, focused on essentials, low performance overhead

---

## Resilience Patterns

### Error Handling: Fail-Fast with Global Handler
**Pattern**: Let errors propagate, catch at global level for 500 responses

```
Request → Handler
            ↓
        Error Occurs
            ↓
        Global Error Handler
            ↓
        500 Response to Client
```

**Implementation**:
- No try/catch blocks within route handlers for expected errors
- Global exception handler at application level catches all unhandled exceptions
- Returns generic 500 error to client
- Logs full error details for debugging
- Application remains running (no crash)

**Benefits**: Simple, clear error flow, centralized error handling

---

## Performance Patterns

### Pagination: Simple Cursor Pattern
**Pattern**: Plain integer cursor (no encoding), position-based pagination

```
Request: GET /posts?cursor=5&limit=20
Response:
{
  "items": [post6, post7, ..., post25],
  "next_cursor": 26,
  "has_more": true
}
```

**Implementation**:
- Cursor is the post ID to start after
- Plain decimal number (no Base64 or JWT encoding)
- Query: `SELECT * FROM posts WHERE id > cursor ORDER BY id LIMIT limit`
- Next cursor is the ID of the last item returned

**Benefits**: Simple, no encoding overhead, efficient with indexes

---

### Tag Filtering: Eager Loading in Python
**Pattern**: Load all posts with tags, filter in application layer

```
1. Load all posts with relationships
   SELECT * FROM posts
   SELECT * FROM tags WHERE post_id IN (...)

2. Filter in Python
   filtered_posts = [p for p in posts if tag_name in p.tag_names]

3. Apply pagination
   return filtered_posts[cursor:cursor+limit]
```

**Implementation**:
- Query posts and eagerly load their tags using SQLModel relationships
- Filter by tag name in Python after loading
- Apply cursor-based pagination on filtered results
- Inefficient for large datasets but simple for development

**Benefits**: Simple, no complex SQL joins, easy to debug, sufficient for < 100 requests/day

---

### Concurrent Request Handling: Last-Write-Wins
**Pattern**: Later updates overwrite earlier ones, no locking or versioning

```
Time 1: Client A updates post (title: "A", content: "X")
Time 2: Client B updates post (title: "B", content: "Y")

Result: Post has title="B", content="Y" (B's update wins)
```

**Implementation**:
- No version tracking
- No optimistic or pessimistic locking
- Simple UPDATE query replaces all values
- Last write always wins
- Suitable for low-concurrency development environment

**Benefits**: Simplest implementation, no state management, works for single-user development

---

## Testing Patterns

### Test Organization: Single File
**Pattern**: All tests in one or two consolidated test files

```
tests/
├── test_api.py          # All endpoint tests
└── test_api_pbt.py      # All property-based tests
```

**Implementation**:
- `test_api.py`: Example-based tests for all endpoints and scenarios
- `test_api_pbt.py`: Property-based tests for data models and endpoints
- No separation by layer (API, business, database)
- Simple to navigate, all related tests together

**Benefits**: Single location to understand all test coverage, easier to run specific tests

---

### Property-Based Testing Scope: Models Only
**Pattern**: PBT for data model serialization/deserialization, not endpoints or business logic

**Models to Test**:
```
✓ BlogPost serialization round-trip
✓ Tag serialization round-trip
✓ Pagination response structure
✗ API endpoints (example-based tests only)
✗ Business logic (example-based tests only)
```

**Implementation**:
- Hypothesis generators for BlogPost and Tag models
- Round-trip property: `deserialize(serialize(obj)) == obj`
- Invariant properties: Model fields match constraints
- Example-based tests cover endpoint behavior
- Example-based tests cover business logic (list, filter, pagination)

**Benefits**: Focused coverage, combines PBT for data models with example-based for endpoints

---

## Summary

| Pattern | Decision |
|---------|----------|
| Validation | Single-layer Pydantic at request level |
| SQL Safety | ORM-only, no raw SQL |
| Error Recovery | Fail-fast, no retries |
| Error Format | Basic (status code + message) |
| Logging | Minimal (path + status code) |
| Error Handling | Global handler for unhandled exceptions |
| Pagination | Plain integer cursor |
| Tag Filtering | Eager load + Python filter |
| Concurrency | Last-write-wins |
| Test Organization | Single test files (API + PBT) |
| PBT Scope | Models only (serialization) |

All patterns prioritize **simplicity and minimal complexity** while maintaining security and functionality.
