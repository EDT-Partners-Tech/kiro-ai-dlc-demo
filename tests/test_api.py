"""Example-based tests for CloudSpend Analytics API."""

import pytest
import os
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

# Use in-memory database for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import init_db, get_session
from main import app

# Create test engine with in-memory database
test_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def get_test_session():
    """Override dependency to use test session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Initialize database before each test and clean up after."""
    # Create tables
    SQLModel.metadata.create_all(test_engine)
    
    # Override the dependency
    app.dependency_overrides[get_session] = get_test_session
    
    yield
    
    # Cleanup
    SQLModel.metadata.drop_all(test_engine)
    app.dependency_overrides.clear()


client = TestClient(app)


# ============================================================================
# Health Check Tests
# ============================================================================

def test_health_check():
    """Test liveness probe."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_check():
    """Test readiness probe."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_root_endpoint():
    """Test root API info."""
    response = client.get("/")
    assert response.status_code == 200
    assert "CloudSpend" in response.json()["name"]


# ============================================================================
# Cost Ingestion Tests
# ============================================================================

def test_create_cost_valid():
    """Test creating a valid cost entry."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "150.50",
        "timestamp": now,
        "tags": ["production", "web"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["service"] == "EC2"
    assert data["amount"] == "150.50"
    assert "production" in data["tags"]


def test_create_cost_invalid_amount_negative():
    """Test reject negative amounts."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "-100.00",
        "timestamp": now
    })
    assert response.status_code == 422  # Pydantic validation error


def test_create_cost_invalid_service():
    """Test reject invalid service names."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2@invalid",
        "amount": "100.00",
        "timestamp": now
    })
    assert response.status_code == 422


def test_create_cost_future_timestamp():
    """Test reject future timestamps."""
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "100.00",
        "timestamp": future
    })
    assert response.status_code == 422


def test_create_cost_with_tags():
    """Test cost creation with tags."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "S3",
        "amount": "45.25",
        "timestamp": now,
        "tags": ["storage", "prod"]
    })
    assert response.status_code == 201
    assert set(response.json()["tags"]) == {"storage", "prod"}


# ============================================================================
# Daily Trends Tests
# ============================================================================

def test_get_daily_trends_empty():
    """Test daily trends with no data."""
    response = client.get("/cost-data/daily")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0


def test_get_daily_trends_with_data():
    """Test daily trends returns aggregates."""
    now = datetime.now(timezone.utc)
    for i in range(3):
        ts = (now - timedelta(days=i)).isoformat()
        client.post("/cost-data", json={
            "service": "EC2",
            "amount": f"{100 + i * 10}.00",
            "timestamp": ts
        })
    
    response = client.get("/cost-data/daily")
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 3


def test_get_daily_trends_service_filter():
    """Test daily trends filtered by service."""
    now = datetime.now(timezone.utc).isoformat()
    client.post("/cost-data", json={
        "service": "RDS",
        "amount": "200.00",
        "timestamp": now
    })
    
    response = client.get("/cost-data/daily?service=RDS")
    assert response.status_code == 200


def test_get_daily_trends_pagination():
    """Test daily trends pagination."""
    response = client.get("/cost-data/daily?limit=5")
    assert response.status_code == 200
    assert response.json()["items_count"] <= 5


# ============================================================================
# Anomaly Detection Tests
# ============================================================================

def test_get_anomalies_empty():
    """Test anomalies with insufficient data."""
    response = client.get("/cost-data/anomalies")
    assert response.status_code == 200
    # Should return empty or data with bootstrap handling
    assert isinstance(response.json()["anomalies"], list)


def test_get_anomalies_service_filter():
    """Test anomalies filtered by service."""
    response = client.get("/cost-data/anomalies?service=EC2")
    assert response.status_code == 200


# ============================================================================
# Recommendation Tests
# ============================================================================

def test_list_recommendations_empty():
    """Test listing recommendations (initially empty or pre-loaded)."""
    response = client.get("/optimization/recommendations")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_list_recommendations_service_filter():
    """Test recommendations filtered by service."""
    response = client.get("/optimization/recommendations?service=EC2")
    assert response.status_code == 200


def test_list_recommendations_status_filter():
    """Test recommendations filtered by status."""
    response = client.get("/optimization/recommendations?status=recommended")
    assert response.status_code == 200


def test_list_recommendations_invalid_status():
    """Test reject invalid status filter."""
    response = client.get("/optimization/recommendations?status=invalid")
    assert response.status_code == 400


# ============================================================================
# Security Tests
# ============================================================================

def test_security_headers_present():
    """Test security headers are added."""
    response = client.get("/health")
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-Content-Type-Options" in response.headers
    assert "X-Request-ID" in response.headers


def test_error_no_stack_trace():
    """Test error responses don't expose stack traces."""
    response = client.post("/cost-data", json={
        "service": "invalid@service",
        "amount": "100.00",
        "timestamp": "invalid"
    })
    assert response.status_code >= 400
    # Should not contain traceback
    assert "traceback" not in response.text.lower()


# ============================================================================
# Delete Tests
# ============================================================================

def test_delete_cost_not_found():
    """Test delete non-existent cost."""
    response = client.delete("/cost-data/invalid-id")
    assert response.status_code == 404


def test_delete_cost_success():
    """Test delete existing cost."""
    now = datetime.now(timezone.utc).isoformat()
    create_response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "100.00",
        "timestamp": now
    })
    assert create_response.status_code == 201
    
    cost_id = create_response.json()["id"]
    delete_response = client.delete(f"/cost-data/{cost_id}")
    assert delete_response.status_code == 204
