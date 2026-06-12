# Build Instructions - Blog Posts API

## Prerequisites

- Python 3.9+
- pip (or poetry/pipenv)

## Step 1: Install Dependencies

### Using pip

```bash
python3 -m pip install --break-system-packages -r requirements.txt
```

Or if not on macOS with system Python:

```bash
python3 -m pip install -r requirements.txt
```

### Using poetry

```bash
poetry install
```

### Verify Installation

```bash
python3 -c "import fastapi, sqlmodel, uvicorn; print('✓ Dependencies installed successfully')"
```

## Step 2: Verify Application Import

```bash
python3 -c "from main import app; from app.models import BlogPost, Tag; print('✓ Application imports successfully')"
```

## Step 3: Build Artifacts

No explicit build step is required. The application is a Python FastAPI app that runs directly.

### Optional: Generate requirements lock file

```bash
pip freeze > requirements-frozen.lock
```

## Application Structure

```
blog-posts-api/
├── main.py                      # FastAPI app entry point
├── app/
│   ├── __init__.py
│   ├── models.py               # Data models and schemas
│   ├── database.py             # Database configuration
│   └── api/
│       ├── __init__.py
│       └── endpoints.py        # Route handlers
├── tests/
│   ├── __init__.py
│   ├── test_api.py            # Example-based tests
│   └── test_api_pbt.py        # Property-based tests
├── docs/
│   ├── README.md              # Project documentation
│   └── API.md                 # API specification
├── pyproject.toml             # Project config
├── requirements.txt           # Dependencies
└── .gitignore                 # Git ignores
```

## Database Setup

The database is automatically created on first run:

```bash
uvicorn main:app
```

This will:
1. Create SQLite database file: `blog-posts.db`
2. Create tables: `blog_posts`, `tags`, `post_tags`
3. Initialize application

## Troubleshooting

### ModuleNotFoundError

If you get `ModuleNotFoundError: No module named 'fastapi'`, ensure dependencies are installed:

```bash
python3 -m pip install -r requirements.txt
```

### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
uvicorn main:app --port 8001
```

### Database Locked

If you get "database is locked" error, ensure only one instance is running:

```bash
pkill -f uvicorn
```

Then restart the application.

### Clean Rebuild

To start fresh:

```bash
rm blog-posts.db
python3 -m pip install -r requirements.txt --force-reinstall
```

## Deployment Preparation

Before deploying to production:

1. **Use environment variables** for configuration
   - Database URL
   - Port
   - Debug mode
   
2. **Use a production ASGI server** (not uvicorn development server)
   - gunicorn with uvicorn workers
   - or Hypercorn

3. **Set DEBUG=False** in production

4. **Use PostgreSQL** instead of SQLite (for concurrency)

5. **Run migrations** (if using Alembic)

6. **Enable logging** to a centralized service

7. **Configure monitoring** and alerting

## Example Production Startup

```bash
# Using gunicorn with uvicorn workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Docker Deployment

See `Dockerfile` (if created) for containerized deployment.
