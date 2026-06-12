# Blog Posts API

A minimal REST API for managing blog posts with tag support, built with FastAPI and SQLite.

## Features

- **CRUD Operations**: Create, read, list, update, and delete blog posts
- **Tag Management**: Associate tags with blog posts
- **Pagination**: Cursor-based pagination for the list endpoint
- **Tag Filtering**: Filter posts by tag on the list endpoint
- **Input Validation**: Automatic validation of all request data via Pydantic
- **Error Handling**: Consistent error responses with appropriate HTTP status codes
- **Security**: HTTP security headers, SQL injection prevention, input sanitization
- **Testing**: Comprehensive example-based and property-based tests

## Requirements

- Python 3.9 or higher
- pip or poetry

## Installation

### Using pip

```bash
# Clone or navigate to the project directory
cd blog-posts-api

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using poetry

```bash
poetry install
```

## Running the API

### Using uvicorn directly

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Using Python module

```bash
python -m uvicorn main:app --reload
```

## API Endpoints

All endpoints are available at `http://localhost:8000/posts`

### Create Blog Post

```
POST /posts
```

Request body:
```json
{
  "title": "My Blog Post",
  "content": "This is the content of my blog post.",
  "tags": ["python", "fastapi"]
}
```

Response (201 Created):
```json
{
  "id": 1,
  "title": "My Blog Post",
  "content": "This is the content of my blog post.",
  "tags": [
    {"id": 1, "name": "python"},
    {"id": 2, "name": "fastapi"}
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Get Blog Post

```
GET /posts/{id}
```

Response (200 OK):
```json
{
  "id": 1,
  "title": "My Blog Post",
  "content": "This is the content of my blog post.",
  "tags": [
    {"id": 1, "name": "python"},
    {"id": 2, "name": "fastapi"}
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### List Blog Posts

```
GET /posts?cursor=<cursor>&limit=<limit>&tag=<tag>
```

Query parameters:
- `cursor` (optional): Cursor for pagination (post ID to start after)
- `limit` (optional): Number of items per page (default: 20, max: 100)
- `tag` (optional): Filter posts by tag name

Response (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "title": "My Blog Post",
      "content": "This is the content of my blog post.",
      "tags": [
        {"id": 1, "name": "python"}
      ],
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "next_cursor": 2,
  "has_more": true
}
```

### Update Blog Post

```
PATCH /posts/{id}
```

Request body (all fields optional):
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "tags": ["python", "updated"]
}
```

Response (200 OK):
```json
{
  "id": 1,
  "title": "Updated Title",
  "content": "Updated content",
  "tags": [
    {"id": 1, "name": "python"},
    {"id": 3, "name": "updated"}
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

### Delete Blog Post

```
DELETE /posts/{id}
```

Response (204 No Content)

## Testing

### Install test dependencies

```bash
pip install -r requirements.txt[dev]
# or
pip install pytest pytest-asyncio httpx hypothesis
```

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=app --cov-report=html
```

### Run property-based tests only

```bash
pytest tests/test_api_pbt.py
```

### Run example-based tests only

```bash
pytest tests/test_api.py
```

### Run specific test

```bash
pytest tests/test_api.py::test_create_post_success
```

## Database

The API uses SQLite for persistence. The database file (`blog-posts.db`) is automatically created in the project root on first run.

### Database Schema

**blog_posts table:**
- `id` (INTEGER PRIMARY KEY)
- `title` (TEXT, max 500 chars)
- `content` (TEXT, max 10000 chars)
- `created_at` (DATETIME)
- `updated_at` (DATETIME)

**tags table:**
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT, max 50 chars, UNIQUE)

**post_tags junction table:**
- `post_id` (FOREIGN KEY)
- `tag_id` (FOREIGN KEY)

### Resetting the database

Simply delete the `blog-posts.db` file and restart the application:

```bash
rm blog-posts.db
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Error Handling

All errors return consistent JSON responses:

```json
{
  "detail": "Error message describing the issue"
}
```

Common HTTP status codes:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Validation

The API validates all input:

- **Title**: Required, non-empty, max 500 characters
- **Content**: Required, non-empty, max 10000 characters
- **Tags**: Optional, each tag max 50 characters, max 10 tags per post

## Security

The API implements the following security measures:

- **HTTP Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **Input Validation**: All requests validated server-side via Pydantic
- **SQL Injection Prevention**: Uses SQLModel ORM with parameterized queries
- **Error Handling**: No internal details exposed in error responses
- **Logging**: Request logging without sensitive data exposure

## Development

### Code Quality

The project uses:
- `black`: Code formatting
- `ruff`: Linting
- `mypy`: Type checking

Run checks:

```bash
black .
ruff check .
mypy .
```

### Project Structure

```
blog-posts-api/
├── main.py                  # FastAPI application entry point
├── app/
│   ├── __init__.py
│   ├── models.py           # Data models
│   ├── database.py         # Database configuration
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py    # API route handlers
│   └── config.py           # Application configuration
├── tests/
│   ├── __init__.py
│   ├── test_api.py         # Example-based tests
│   └── test_api_pbt.py     # Property-based tests
├── docs/
│   ├── README.md           # This file
│   └── API.md              # API documentation
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
├── .python-version         # Python version specification
└── .gitignore              # Git ignore rules
```

## Future Improvements

- User authentication and authorization
- Database migrations (Alembic)
- Rate limiting
- Caching layer (Redis)
- Async database driver (async SQLite)
- Docker containerization
- CI/CD pipeline
- API versioning
- More advanced filtering and search
- Batch operations
- Webhooks for post events

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please create an issue on the project repository.
