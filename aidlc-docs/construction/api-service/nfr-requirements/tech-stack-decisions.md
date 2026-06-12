# Tech Stack Decisions - API Service

## Framework & Runtime

### Python
- **Version**: Python 3.9+ (supports modern async/await, type hints, pattern matching)
- **Rationale**: Specified in requirements, suitable for REST APIs, good FastAPI support
- **Decision**: Use Python 3.10 or higher for better type hint support

### FastAPI
- **Version**: Latest stable (currently 0.104+)
- **Rationale**: Modern async web framework, excellent for REST APIs, built-in OpenAPI docs, type hint support, minimal boilerplate
- **Key Features Used**:
  - Async request handlers
  - Dependency injection for database session management
  - Automatic OpenAPI documentation
  - Built-in validation via Pydantic

### SQLModel
- **Version**: Latest stable
- **Rationale**: Bridges FastAPI and SQLAlchemy, provides ORM and Pydantic models in one, excellent type support
- **Key Features Used**:
  - Models as both database ORM and API request/response schemas
  - Automatic validation and serialization
  - Relationship management (Blog Post ↔ Tags)

### SQLite
- **Database**: SQLite 3.x (included with Python)
- **File Location**: `./blog-posts.db` (project directory)
- **Rationale**: Specified in requirements, zero configuration, suitable for development/prototype, file-based persistence
- **Connection**: Single connection with basic configuration

---

## Dependency Selection

### Core Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| fastapi | Web framework | >=0.104.0 |
| sqlmodel | ORM + Pydantic models | >=0.0.14 |
| uvicorn | ASGI server | >=0.24.0 |
| pydantic | Data validation | >=2.0 |
| sqlalchemy | Database abstraction | >=2.0 |

### Testing Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| pytest | Test framework | >=7.4.0 |
| pytest-asyncio | Async test support | >=0.21.0 |
| httpx | HTTP client for testing | >=0.25.0 |
| hypothesis | Property-based testing | >=6.82.0 |

### Development Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| black | Code formatting | >=23.0 |
| ruff | Linting | >=0.1.0 |
| mypy | Type checking | >=1.5.0 |
| pytest-cov | Coverage reporting | >=4.1.0 |

---

## Database Design

### Connection Strategy
- **Type**: Single SQLite connection
- **Pooling**: None (development phase)
- **Threading**: Single-threaded context per request
- **Connection String**: `sqlite:///./blog-posts.db`

### Schema Design
- **Blog Posts Table**: Stores blog post data (id, title, content, created_at, updated_at)
- **Tags Table**: Stores unique tags (id, name)
- **Post_Tags Junction Table**: Many-to-many relationship between posts and tags

### Relationship Management
- **Blog Post ↔ Tags**: Many-to-many relationship via junction table
- **ORM Handling**: SQLModel manages relationship through relationship() declarations
- **Cascade Behavior**: Soft cascades (manual cleanup if tag is deleted)

---

## API Design

### Protocol
- **Protocol**: HTTP/REST
- **Format**: JSON for all request/response bodies
- **Encoding**: UTF-8

### Request/Response Handling
- **Validation**: Pydantic models validate all input
- **Serialization**: SQLModel models automatically serialize to JSON
- **Error Responses**: Standard error format with status code, message, and optional details

### Pagination Implementation
- **Strategy**: Cursor-based pagination
- **Cursor Format**: Base64-encoded post ID
- **Parameters**: `?cursor=<base64_id>&limit=<1-100>`
- **Response Metadata**: `next_cursor`, `has_more`, `items`

---

## Security Implementation

### Input Validation
- **Framework**: Pydantic (built into FastAPI/SQLModel)
- **Validation Rules**:
  - Title: Required, string, non-empty, max 500 chars
  - Content: Required, string, non-empty, max 10000 chars
  - Tags: Optional, list of strings, max 10 tags per post, each max 50 chars
- **Injection Prevention**: SQLModel ORM uses parameterized queries (no string concatenation)

### Error Handling
- **Strategy**: Return generic error messages (no internal details)
- **Error Format**: `{"detail": "error message", "status_code": 400}`
- **Status Codes**: 400, 404, 500 (no stack traces to clients)

### HTTP Security Headers
- **Content-Security-Policy**: `default-src 'self'`
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains`
- **X-Content-Type-Options**: `nosniff`
- **X-Frame-Options**: `DENY`
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Implementation**: Middleware or response decorator

### Logging
- **Format**: Structured logging with timestamp, level, message
- **Output**: Console (stdout/stderr)
- **Sensitive Data**: No passwords, tokens, or PII in logs
- **Library**: Python `logging` module with JSON formatter

---

## Property-Based Testing Framework

### Framework Selection: Hypothesis

**Rationale**:
- Mature Python library with excellent shrinking
- Integrates seamlessly with pytest
- Outstanding documentation and community
- Strong support for domain-specific generators

### Key Usage Areas

#### Round-Trip Properties (PBT-02)
- JSON serialization → deserialization round-trip
- Tests: Pydantic models serialize and deserialize correctly
- Property: `deserialize(serialize(obj)) == obj`

#### Invariant Properties (PBT-03)
- List endpoint pagination invariants
- Tests: Number of items in page, cursor progression
- Properties: Total items consistent, cursors work correctly, no item duplication

#### Generator Development (PBT-07)
- Custom generators for BlogPost, Tag, PaginationParams
- Generators respect business constraints (length limits, valid data)
- Examples: `blog_post_strategy()`, `tag_strategy()`, `pagination_params_strategy()`

### Test Structure
- **Location**: `tests/test_api_pbt.py` (property-based tests)
- **Alongside**: `tests/test_api_example.py` (example-based tests)
- **Configuration**: Hypothesis settings for hypothesis count (100 examples per test)

---

## Dependency Management

### Lock File
- **Tool**: `pip-compile` or `poetry.lock`
- **Location**: `requirements-lock.txt` or `poetry.lock`
- **Pinning**: All dependencies pinned to exact versions
- **Maintenance**: Update lock file quarterly

### Vulnerability Scanning
- **Tool**: `pip-audit` or equivalent
- **Schedule**: On every CI/CD run
- **Action**: Fail build if vulnerabilities found

### No Unused Dependencies
- **Validation**: Regular audit of `requirements.txt` to remove unused packages

---

## Development Setup

### Local Development
- **Python Version**: 3.10+ (verified via `.python-version` or `pyproject.toml`)
- **Virtual Environment**: `venv` or `poetry`
- **Installation**: `pip install -r requirements.txt`
- **Running**: `uvicorn main:app --reload` (auto-reload on changes)

### Database Initialization
- **Approach**: SQLModel auto-creates tables on first run
- **Initialization**: Single `SQLModel.metadata.create_all(engine)` call at startup

### Code Quality
- **Linting**: `ruff check .` (fast Python linter)
- **Formatting**: `black .` (code formatter)
- **Type Checking**: `mypy .` (static type checking)

---

## Deployment Target

### Runtime Environment
- **Target**: Standalone Python process
- **Platform**: Any platform supporting Python 3.9+
- **Server**: Uvicorn ASGI server (simple, suitable for development)

### Configuration
- **Database File**: Relative path `./blog-posts.db` in working directory
- **Environment Variables**: None required for basic setup
- **Port**: Configurable (default 8000)

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Language | Python 3.10+ | Specified, good async support |
| Web Framework | FastAPI | Modern, async, minimal boilerplate |
| ORM | SQLModel | FastAPI-native, type support |
| Database | SQLite file-based | Specified, zero setup |
| Testing | Pytest + Hypothesis | Standard Python testing + PBT |
| Pagination | Cursor-based | Stable, performs well with SQLite |
| Authentication | None (public API) | Development/prototype requirement |
| Monitoring | Console logs | Minimal operational overhead |
| Caching | None | Simple, direct database access |
| Deployment | Standalone Python | Simple, specified in requirements |

---

## Evolution Path

As the project matures:

1. **Production-Grade**: PostgreSQL, connection pooling, centralized logging
2. **Scaling**: Horizontal scaling with multiple instances and load balancer
3. **Monitoring**: Add Prometheus metrics, Grafana dashboards, alerts
4. **Authentication**: Add JWT or API key authentication if needed
5. **Caching**: Redis for hot data
6. **Backup**: Automated backups and recovery procedures

Current setup is optimized for rapid development and learning.
