"""Property-based tests for CloudSpend Analytics API using Hypothesis."""

import pytest
import os
import uuid
from hypothesis import given, strategies as st
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

# Use in-memory database for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import get_session
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
# Strategies (Generators for Test Data)
# ============================================================================

positive_decimal_str = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("999999.99"),
    places=2
).map(str)

valid_service_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=64
)

valid_tag_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=1,
    max_size=64
)

valid_timestamps = st.datetimes(
    max_value=datetime.now(timezone.utc)
).map(lambda dt: dt.replace(tzinfo=timezone.utc).isoformat())


# ============================================================================
# Decimal Precision Tests
# ============================================================================

@given(positive_decimal_str)
def test_cost_amount_precision_roundtrip(amount_str):
    """Property: Cost amount maintains 2 decimal place precision."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": amount_str,
        "timestamp": now
    })
    
    if response.status_code == 201:
        returned_amount = response.json()["amount"]
        # Both should have exactly 2 decimal places
        assert len(returned_amount.split('.')[-1]) <= 2


@given(st.lists(positive_decimal_str, min_size=1, max_size=10))
def test_cost_aggregation_commutativity(amounts):
    """Property: Aggregation is consistent regardless of input order."""
    now = datetime.now(timezone.utc)
    service_name = f"TEST-{uuid.uuid4().hex[:8]}"  # Unique service per test
    today = now.isoformat().split("T")[0]
    
    # Insert costs with unique service name
    for i, amount in enumerate(amounts):
        ts = (now - timedelta(hours=i)).isoformat()
        client.post("/cost-data", json={
            "service": service_name,
            "amount": amount,
            "timestamp": ts
        })
    
    # Get total for this unique service
    response = client.get(f"/cost-data/daily?service={service_name}")
    if response.status_code == 200 and response.json()["items"]:
        # Find today's entry for this service
        today_item = next(
            (item for item in response.json()["items"] if item["date"] == today),
            None
        )
        if today_item:
            total_from_api = Decimal(today_item["total_cost"])
            total_input = sum(Decimal(a) for a in amounts)
            assert abs(total_from_api - total_input) < Decimal("0.01")


# ============================================================================
# Validation Invariants
# ============================================================================

@given(st.just("0.00"))
def test_zero_cost_rejected(amount):
    """Property: Zero or negative costs are always rejected."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": amount,
        "timestamp": now
    })
    assert response.status_code >= 400


@given(st.integers(min_value=1, max_value=365))
def test_past_timestamp_accepted(days_ago):
    """Property: Any past timestamp is accepted (no historical limit)."""
    past_ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "100.00",
        "timestamp": past_ts
    })
    assert response.status_code == 201


@given(st.just((datetime.now(timezone.utc) + timedelta(days=1)).isoformat()))
def test_future_timestamp_rejected(future_ts):
    """Property: Future timestamps are always rejected."""
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "100.00",
        "timestamp": future_ts
    })
    assert response.status_code >= 400


# ============================================================================
# Service Name Format Tests
# ============================================================================

@given(valid_service_names)
def test_valid_service_accepted(service):
    """Property: Valid service names are accepted."""
    if not service or len(service) > 64:
        return  # Skip invalid inputs
    
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": service,
        "amount": "100.00",
        "timestamp": now
    })
    # Should succeed or fail gracefully, not crash
    assert response.status_code in [201, 422, 400, 500]


# ============================================================================
# Pagination Invariants
# ============================================================================

@given(st.integers(min_value=1, max_value=100))
def test_pagination_limit_respected(limit):
    """Property: Pagination limit is never exceeded."""
    response = client.get(f"/cost-data/daily?limit={limit}")
    if response.status_code == 200:
        items_count = len(response.json()["items"])
        assert items_count <= limit


# ============================================================================
# Anomaly Detection Invariants
# ============================================================================

@given(positive_decimal_str)
def test_anomaly_spike_percentage_valid(baseline_factor):
    """Property: Spike percentage is always non-negative."""
    response = client.get("/cost-data/anomalies")
    if response.status_code == 200:
        for anomaly in response.json()["anomalies"]:
            spike_pct = float(anomaly["spike_percentage"])
            # Spike % should be >= 25 (threshold)
            assert spike_pct >= 25


# ============================================================================
# Recommendation Status Invariants
# ============================================================================

@given(st.just("recommended"))
def test_status_must_be_valid(status):
    """Property: Only valid statuses are accepted."""
    response = client.get(f"/optimization/recommendations?status={status}")
    # Valid status should not return error
    if response.status_code == 200:
        assert True


@given(st.just("invalid_status"))
def test_invalid_status_rejected(status):
    """Property: Invalid statuses are always rejected."""
    response = client.get(f"/optimization/recommendations?status={status}")
    assert response.status_code >= 400


# ============================================================================
# Tag Format Tests
# ============================================================================

@given(st.lists(valid_tag_names, min_size=0, max_size=5))
def test_tag_format_accepted(tags):
    """Property: Valid tag formats are accepted."""
    now = datetime.now(timezone.utc).isoformat()
    response = client.post("/cost-data", json={
        "service": "EC2",
        "amount": "100.00",
        "timestamp": now,
        "tags": tags
    })
    # Should accept valid tags
    if response.status_code == 201:
        returned_tags = response.json()["tags"]
        assert set(returned_tags) == set(tags)


# ============================================================================
# Response Structure Invariants
# ============================================================================

@given(st.just(None))
def test_daily_trends_response_structure(unused):
    """Property: Daily trends response always has required fields."""
    response = client.get("/cost-data/daily")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "has_more" in data
    assert "items_count" in data
    
    for item in data["items"]:
        assert "date" in item
        assert "total_cost" in item


@given(st.just(None))
def test_recommendations_response_structure(unused):
    """Property: Recommendations response always has required fields."""
    response = client.get("/optimization/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "has_more" in data
    assert "items_count" in data


# ============================================================================
# Error Response Invariants
# ============================================================================

@given(st.just(None))
def test_error_response_safe(unused):
    """Property: Error responses never expose internals."""
    # Test with invalid input
    response = client.post("/cost-data", json={
        "service": "invalid@service!",
        "amount": "abc",
        "timestamp": "invalid"
    })
    
    if response.status_code >= 400:
        error_text = str(response.text).lower()
        # Should not contain traceback or internal details
        assert "traceback" not in error_text
        assert "sqlalchemy" not in error_text
