"""FastAPI application for Blog Posts API."""

import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse

from app.api.endpoints import router
from app.database import create_db_and_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app with docs disabled (we'll serve them manually)
app = FastAPI(
    title="Blog Posts API",
    description="A minimal REST API for managing blog posts with tag support",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

# ============================================================================
# Custom Docs HTML - Simple version that doesn't require external CDN
# ============================================================================


@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
async def docs():
    """Swagger UI documentation."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blog Posts API - Swagger UI</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
        <style>
            html{box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll;}
            *,*:before,*:after{box-sizing: inherit;}
            body{margin:0;padding:0;}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.json",
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    layout: "StandaloneLayout"
                })
            }
        </script>
    </body>
    </html>
    """


@app.get("/redoc", include_in_schema=False, response_class=HTMLResponse)
async def redoc():
    """ReDoc documentation."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blog Posts API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url='/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """


# ============================================================================
# Middleware - Security Headers
# ============================================================================


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers per SECURITY-04 - Allow CDN for docs
    response.headers["Content-Security-Policy"] = "default-src 'self' https: data: 'unsafe-inline'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# ============================================================================
# Middleware - Request Logging
# ============================================================================


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each API request with method, path, and status code."""
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response


# ============================================================================
# Global Exception Handler
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# Startup and Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    create_db_and_tables()
    logger.info("Database initialized")
    logger.info("API available at http://localhost:8000")
    logger.info("Documentation at http://localhost:8000/docs")


# ============================================================================
# Override OpenAPI Schema Generation - Force OpenAPI 3.0.2 for Swagger UI
# ============================================================================


def custom_openapi():
    """Generate OpenAPI schema in 3.0.2 format for Swagger UI compatibility."""
    from fastapi.openapi.utils import get_openapi
    from copy import deepcopy
    
    if app.openapi_schema:
        return app.openapi_schema
    
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Force OpenAPI 3.0.2 for Swagger UI compatibility
    schema["openapi"] = "3.0.2"
    
    # Remove any 3.1.0-specific features that break older Swagger UI
    if "webhooks" in schema:
        del schema["webhooks"]
    
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================================
# Routes
# ============================================================================

app.include_router(router)


# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", tags=["info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Blog Posts API",
        "version": "1.0.0",
        "description": "A minimal REST API for managing blog posts with tag support",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


