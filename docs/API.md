# Blog Posts API - Endpoint Specification

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Create Blog Post

Create a new blog post.

**Endpoint:** `POST /posts`

**Request Body:**
```json
{
  "title": "string (required, max 500 chars)",
  "content": "string (required, max 10000 chars)",
  "tags": ["string"] (optional, max 10 tags, each max 50 chars)
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Getting Started with FastAPI",
    "content": "FastAPI is a modern, fast web framework for building APIs...",
    "tags": ["fastapi", "python", "web"]
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Getting Started with FastAPI",
  "content": "FastAPI is a modern, fast web framework for building APIs...",
  "tags": [
    {"id": 1, "name": "fastapi"},
    {"id": 2, "name": "python"},
    {"id": 3, "name": "web"}
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data
  ```json
  {"detail": "title must be non-empty"}
  ```

- `500 Internal Server Error`: Server error
  ```json
  {"detail": "Internal server error"}
  ```

---

### 2. Get Blog Post

Retrieve a single blog post by ID.

**Endpoint:** `GET /posts/{id}`

**Path Parameters:**
- `id` (integer, required): The blog post ID

**Example Request:**
```bash
curl http://localhost:8000/posts/1
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Getting Started with FastAPI",
  "content": "FastAPI is a modern, fast web framework for building APIs...",
  "tags": [
    {"id": 1, "name": "fastapi"},
    {"id": 2, "name": "python"},
    {"id": 3, "name": "web"}
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**

- `404 Not Found`: Blog post not found
  ```json
  {"detail": "Post not found"}
  ```

---

### 3. List Blog Posts

List blog posts with cursor-based pagination and optional tag filtering.

**Endpoint:** `GET /posts`

**Query Parameters:**
- `cursor` (integer, optional): Post ID to start pagination after (default: start from beginning)
- `limit` (integer, optional): Number of items per page (default: 20, max: 100)
- `tag` (string, optional): Filter posts by tag name

**Example Requests:**

List all posts (default pagination):
```bash
curl http://localhost:8000/posts
```

List with custom limit:
```bash
curl http://localhost:8000/posts?limit=10
```

List with pagination cursor:
```bash
curl http://localhost:8000/posts?cursor=5&limit=10
```

Filter by tag:
```bash
curl http://localhost:8000/posts?tag=python
```

Combine pagination and filtering:
```bash
curl http://localhost:8000/posts?cursor=5&limit=10&tag=python
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Getting Started with FastAPI",
      "content": "FastAPI is a modern, fast web framework...",
      "tags": [
        {"id": 1, "name": "fastapi"},
        {"id": 2, "name": "python"}
      ],
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "title": "Python Best Practices",
      "content": "Here are some Python best practices...",
      "tags": [
        {"id": 2, "name": "python"}
      ],
      "created_at": "2024-01-15T10:35:00",
      "updated_at": "2024-01-15T10:35:00"
    }
  ],
  "next_cursor": 3,
  "has_more": true
}
```

**Pagination Details:**

- `items`: Array of blog posts for the current page
- `next_cursor`: ID to use for the next page (null if no more pages)
- `has_more`: Boolean indicating if more pages exist

To fetch the next page, use the `next_cursor` value as the `cursor` parameter in the next request.

**Empty Result Response:**
```json
{
  "items": [],
  "next_cursor": null,
  "has_more": false
}
```

---

### 4. Update Blog Post

Update a blog post (partial update supported).

**Endpoint:** `PATCH /posts/{id}`

**Path Parameters:**
- `id` (integer, required): The blog post ID

**Request Body (all fields optional):**
```json
{
  "title": "string (optional, max 500 chars)",
  "content": "string (optional, max 10000 chars)",
  "tags": ["string"] (optional, replaces all tags)
}
```

**Example Request:**
```bash
curl -X PATCH http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated FastAPI Guide",
    "tags": ["fastapi", "python", "updated"]
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Updated FastAPI Guide",
  "content": "FastAPI is a modern, fast web framework...",
  "tags": [
    {"id": 1, "name": "fastapi"},
    {"id": 2, "name": "python"},
    {"id": 4, "name": "updated"}
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:40:00"
}
```

**Note:** The `updated_at` timestamp is automatically updated with every modification.

**Error Responses:**

- `404 Not Found`: Blog post not found
  ```json
  {"detail": "Post not found"}
  ```

- `400 Bad Request`: Invalid input data
  ```json
  {"detail": "title must be non-empty"}
  ```

---

### 5. Delete Blog Post

Delete a blog post.

**Endpoint:** `DELETE /posts/{id}`

**Path Parameters:**
- `id` (integer, required): The blog post ID

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/posts/1
```

**Response (204 No Content)**

No response body.

**Error Responses:**

- `404 Not Found`: Blog post not found
  ```json
  {"detail": "Post not found"}
  ```

---

## Data Models

### Blog Post

```typescript
{
  id: integer,                     // Auto-generated, unique identifier
  title: string,                   // Max 500 characters
  content: string,                 // Max 10000 characters
  tags: Tag[],                     // Array of Tag objects
  created_at: ISO 8601 datetime,   // Auto-generated on creation
  updated_at: ISO 8601 datetime    // Auto-generated on creation, updated on modification
}
```

### Tag

```typescript
{
  id: integer,            // Auto-generated, unique identifier
  name: string            // Tag name, max 50 characters
}
```

### Pagination Response

```typescript
{
  items: BlogPost[],          // Array of blog posts
  next_cursor: integer | null,  // Cursor for next page (null if no more)
  has_more: boolean            // Whether more pages exist
}
```

---

## Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful GET or PATCH request |
| 201 | Created | Successful POST request (resource created) |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid request data (validation error) |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Validation Rules

| Field | Rules |
|-------|-------|
| `title` | Required, non-empty, max 500 characters |
| `content` | Required, non-empty, max 10000 characters |
| `tags` | Optional, each tag max 50 characters, max 10 tags per post |
| `id` | Positive integer |
| `cursor` | Positive integer or null |
| `limit` | Integer between 1 and 100 |

---

## Pagination Example

**Step 1: Get first page**
```bash
curl http://localhost:8000/posts?limit=2
```

Response:
```json
{
  "items": [
    {"id": 1, "title": "Post 1", ...},
    {"id": 2, "title": "Post 2", ...}
  ],
  "next_cursor": 2,
  "has_more": true
}
```

**Step 2: Get next page using cursor**
```bash
curl http://localhost:8000/posts?cursor=2&limit=2
```

Response:
```json
{
  "items": [
    {"id": 3, "title": "Post 3", ...},
    {"id": 4, "title": "Post 4", ...}
  ],
  "next_cursor": 4,
  "has_more": true
}
```

**Step 3: Get final page**
```bash
curl http://localhost:8000/posts?cursor=4&limit=2
```

Response:
```json
{
  "items": [
    {"id": 5, "title": "Post 5", ...}
  ],
  "next_cursor": null,
  "has_more": false
}
```

---

## Tag Filtering Example

**Get all posts (unfiltered)**
```bash
curl http://localhost:8000/posts
```

**Filter posts by tag "python"**
```bash
curl http://localhost:8000/posts?tag=python
```

Only posts that have the "python" tag will be returned.

**Combine filtering with pagination**
```bash
curl http://localhost:8000/posts?tag=python&limit=10&cursor=5
```

Returns up to 10 Python-tagged posts, starting after post with ID 5.

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Use these to interactively explore and test the API.
