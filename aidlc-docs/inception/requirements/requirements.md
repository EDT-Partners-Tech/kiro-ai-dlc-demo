# Blog Posts API - Requirements Document

## Intent Analysis

### User Request
Build a minimal REST API for managing blog posts with tag support using FastAPI and SQLite (SQLModel). The API should expose five core operations: create, read, list (with pagination and tag filtering), update, and delete.

### Request Type
New Project (Greenfield) - Building a new REST API application from scratch

### Scope Estimate
Single Component - REST API service with database persistence

### Complexity Estimate
Moderate - Multiple operations with specific requirements for pagination, filtering, and error handling

### Extensions Enabled
- **Security Baseline**: Yes (production-grade security enforcement)
- **Property-Based Testing**: Yes (all PBT rules as blocking constraints)

---

## Functional Requirements

### FR-1: Blog Post Data Model
The API must manage blog posts with the following attributes:
- **id**: Unique identifier (auto-generated)
- **title**: Blog post title (required)
- **content**: Blog post body content (required)
- **tags**: List of associated tags (optional, many-to-many relationship)
- **created_at**: Timestamp of creation (auto-generated)
- **updated_at**: Timestamp of last update (auto-generated)

### FR-2: Core Operations

#### FR-2.1: Create Operation (POST /posts)
- Accept blog post data (title, content, tags)
- Validate input (basic validation: required fields, non-empty)
- Create new blog post with auto-generated id, created_at, updated_at
- Return created post with full details and HTTP 201 Created

#### FR-2.2: Read Operation (GET /posts/{id})
- Retrieve a single blog post by ID
- Return full post details including tags
- Return HTTP 200 OK on success or HTTP 404 Not Found if post doesn't exist

#### FR-2.3: List Operation (GET /posts)
- Return paginated list of blog posts
- **Pagination Strategy**: Cursor-based pagination
- **Default Page Size**: 20
- **Maximum Page Size**: 100
- **Filtering**: Support filtering by a single tag
- **Response Metadata**: Include pagination info (next cursor, has_more)
- Return HTTP 200 OK with paginated results

#### FR-2.4: Update Operation (PATCH /posts/{id})
- Accept partial blog post data (title, content, tags)
- Validate input (basic validation)
- Update specified fields on existing post
- Auto-update the updated_at timestamp
- Return updated post or HTTP 404 Not Found if post doesn't exist
- Return HTTP 200 OK on success

#### FR-2.5: Delete Operation (DELETE /posts/{id})
- Delete a blog post by ID
- Return HTTP 204 No Content on success
- Return HTTP 404 Not Found if post doesn't exist

### FR-3: Tag Filtering
- List endpoint must support filtering by a single tag
- Posts matching the tag should be returned in the paginated results
- If tag doesn't exist or no posts have the tag, return empty list with valid pagination metadata

### FR-4: Tag Management
- Tags are associated with posts in a many-to-many relationship
- Tags are created implicitly when referenced in post creation/update
- Tags should be stored separately from posts

---

## Non-Functional Requirements

### NFR-1: Error Handling
- **Strategy**: Standard REST error handling with detailed error messages
- **HTTP Status Codes**:
  - 200 OK - Successful GET/PATCH
  - 201 Created - Successful POST
  - 204 No Content - Successful DELETE
  - 400 Bad Request - Invalid input
  - 404 Not Found - Resource not found
  - 500 Internal Server Error - Unhandled server errors
- **Error Response Format**: Include error message, optional error details
- No stack traces or internal system details in production error responses

### NFR-2: Performance
- List endpoint pagination with cursor-based approach for consistent performance
- Database queries should be optimized to avoid N+1 queries
- Response time target: <500ms for list operations (at typical scale)

### NFR-3: Data Persistence
- SQLite database with SQLModel ORM
- Database should be file-based in the workspace directory
- Support concurrent read access

### NFR-4: API Response Format
- JSON format for all responses
- **Response Metadata**: Minimal metadata (pagination info for list responses only)
  - For list responses: include cursor, has_more, items_count fields
  - No timestamps or API version in responses (minimal approach per user requirement)

### NFR-5: Validation
- **Input Validation**:
  - Title: Required, non-empty string
  - Content: Required, non-empty string
  - Tags: Optional list of strings
  - Use basic validation (required field checks, non-empty checks)
  - No HTML escaping or advanced sanitization (basic approach per user requirement)
- All validation performed server-side

### NFR-6: Framework and Stack
- **Web Framework**: FastAPI
- **ORM**: SQLModel
- **Database**: SQLite
- **Language**: Python 3.9+
- **Deployment**: Standalone Python process

---

## API Endpoint Summary

| Operation | Method | Path | Input | Output | Status |
|-----------|--------|------|-------|--------|--------|
| Create | POST | /posts | BlogPost (title, content, tags) | Created BlogPost | 201/400 |
| Read | GET | /posts/{id} | ID | BlogPost or error | 200/404 |
| List | GET | /posts?tag=&cursor= | Tag (optional), cursor (optional) | Paginated BlogPost list | 200 |
| Update | PATCH | /posts/{id} | BlogPost partial | Updated BlogPost | 200/404 |
| Delete | DELETE | /posts/{id} | ID | Empty | 204/404 |

---

## Extension Requirements

### Security Baseline (ENABLED)
The following security rules are applicable and must be enforced:
- **SECURITY-05**: Input validation on all API parameters
- **SECURITY-08**: Application-level access control (all endpoints are public, no authentication required)
- **SECURITY-09**: No default credentials or hardcoded secrets
- **SECURITY-15**: Proper error handling with no internal details exposed

### Property-Based Testing (ENABLED - Full Enforcement)
The following PBT rules are applicable and must be enforced:
- **PBT-02**: Round-trip properties for serialization/deserialization
- **PBT-03**: Invariant properties for list operations and pagination
- **PBT-07**: Domain-specific generators for blog posts and tags
- **PBT-09**: Framework selection and configuration (Python: Hypothesis)
- **PBT-10**: Complementary testing strategy (both example-based and property-based tests)

---

## Success Criteria

1. ✅ All five core operations implemented and working
2. ✅ Tag filtering functional on list endpoint
3. ✅ Cursor-based pagination implemented (default 20, max 100)
4. ✅ Proper HTTP status codes and error messages
5. ✅ SQLite database with SQLModel ORM
6. ✅ Comprehensive test coverage including property-based tests
7. ✅ Security and input validation compliance
8. ✅ Code can run as standalone Python process

---

## Technical Decisions

### Cursor-Based Pagination
Chosen over limit/offset pagination for:
- Consistency: Data remains stable even if records are added/deleted during pagination
- Performance: Cursor queries typically use indexed lookups
- API stability: Doesn't expose internal record counts

### Single Tag Filtering
Implemented per user requirement for simplicity. Users can make multiple requests to filter by different tags or combine results client-side.

### Minimal Response Metadata
Only pagination info included in list responses. No timestamps or version info in responses to keep responses lean.

### Basic Validation
Simple validation (required fields, non-empty checks) sufficient for this API's scope. More complex validation can be added if requirements expand.
