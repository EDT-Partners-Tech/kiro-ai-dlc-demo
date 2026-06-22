# NFR Design Patterns - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: NFR Design  
**Date**: 2026-06-19

---

## Overview

This document specifies the non-functional design patterns implemented in the Cost Analytics Service to meet scalability, performance, security, and reliability requirements.

---

## Pattern 1: Layered Input Validation

**Requirement**: Validate all user input per Security Baseline

**Pattern Implementation**:
```
Request → FastAPI Middleware → Pydantic Models → Business Logic
         (structural)          (type/shape)      (business rules)
```

**Layers**:
1. **Middleware Layer**: Global validation (e.g., check for negative amounts before model parsing)
2. **Pydantic Layer**: Type validation (FastAPI auto-parses and validates against models)
3. **Business Logic Layer**: Rule validation (e.g., timestamp not in future, service name alphanumeric)

**Rationale**: Fail fast at earliest layer; clear error messages at each level

**Implementation Details**:
- Pydantic models with `@validator` decorators for complex rules
- Custom exception handlers for validation errors
- HTTP 400 response with human-readable message (no error codes)

---

## Pattern 2: Error Handling & Safe Error Messages

**Requirement**: Return clear errors without exposing internals (Security Baseline)

**Pattern**:
```
Exception (internal) → Exception Handler → Safe Error Response (client)
  ↓
  (database error, validation failure, timeout)
  ↓
  → Map to HTTP status + message
  ↓
  → Log full context (for debugging)
  ↓
  → Return {"error": "human message"} (no internal details)
```

**Error Mapping**:
| Exception | HTTP Status | Client Message |
|-----------|------------|-----------------|
| ValidationError | 400 | "Invalid input: field X" (specific field) |
| ValueError | 400 | "Amount must be positive" (business rule) |
| NotFound | 404 | "Recommendation not found" |
| Timeout | 500 | "Request timed out" |
| Database Error | 500 | "Internal server error" |

**Logging**: Full exception + stack trace logged for developers (not sent to client)

**Rationale**: Users get helpful messages; attackers don't see system internals

---

## Pattern 3: Security Headers

**Requirement**: Protect against common web vulnerabilities

**Implementation** (FastAPI middleware):
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Type"] = "application/json"
    return response
```

**Headers Added**:
- `X-Frame-Options: DENY` — Prevent clickjacking
- `X-Content-Type-Options: nosniff` — Prevent MIME-type confusion
- `Content-Type: application/json` — Explicit content type

**Rationale**: Standard browser protections; minimal overhead

---

## Pattern 4: Stateless API Design

**Requirement**: Enable horizontal scaling (future) without code changes

**Pattern**: 
- No in-memory state (each request is independent)
- No session storage (stateless per request)
- State only in database (consistent across instances)

**Benefits**:
- Any API instance can handle any request
- Easy horizontal scaling (add more instances, no coordination)
- Load balancing becomes trivial (round-robin works)

**Implementation**:
- FastAPI dependency injection (session per request)
- No global state (only dependency-injected state)
- Database as single source of truth

**Rationale**: Costs nothing now; enables scaling later

---

## Pattern 5: Connection Pooling

**Requirement**: Optimize database connections

**Pattern**:
```
Request → Connection Pool (min=5, max=20) → SQLite
          (reuse existing connections)
```

**Rationale**:
- Reuse connections (avoid connection creation overhead)
- Limit simultaneous connections (resource protection)
- Demo scale: pool is overkill, but best practice

**Implementation** (SQLAlchemy):
```python
engine = create_engine(
    database_url,
    pool_size=5,
    max_overflow=15,  # total max = 20
    pool_pre_ping=True  # verify connection before use
)
```

---

## Pattern 6: Request Tracing

**Requirement**: Correlate logs across requests (observability)

**Pattern**:
```
Request → Generate UUID → Middleware adds to context → All logs include request_id
```

**Implementation**:
- Middleware generates `request_id` (UUID)
- Store in `contextvars` (async-safe)
- All logs include `request_id` field
- Response header includes `X-Request-ID` (clients can use for support tickets)

**Rationale**: Debug multi-step issues; correlate logs from one request across time

---

## Pattern 7: Transactional Writes

**Requirement**: Ensure ACID guarantees for financial data

**Pattern**:
```python
@app.post("/cost-data")
def create_cost(cost: CostEntryRequest, db: Session):
    try:
        # All in one transaction
        entry = CostEntry(**cost.dict())
        for tag_name in cost.tags:
            tag = db.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
            entry.tags.append(tag)
        db.add(entry)
        db.commit()  # Atomic: all or nothing
        return entry
    except Exception as e:
        db.rollback()  # Undo if error
        raise
```

**Rationale**: Financial data must be consistent; ACID guarantees compliance

---

## Pattern 8: Graceful Degradation (Anomalies)

**Requirement**: Handle edge cases (insufficient data) gracefully

**Pattern**:
```
Request for anomalies
  ↓
  Check if enough historical data (7 days)
  ↓
  YES → Compute anomalies → Return results
  NO  → Return empty list (no anomalies detected due to insufficient history)
```

**Rationale**: Empty results are semantically clear; errors confuse users

**Implementation**:
```python
@app.get("/cost-data/anomalies")
def get_anomalies(service: Optional[str], db: Session):
    anomalies = []
    # Logic returns [] if < 7 days data
    return {"anomalies": anomalies}
```

---

## Pattern 9: Health Checks (Liveness & Readiness)

**Requirement**: Enable load balancers to route traffic intelligently

**Pattern**:
```
GET /health           → Quick 200 OK (liveness: "I'm alive")
GET /health/ready     → Verify DB + dependencies (readiness: "I can serve requests")
```

**Implementation**:
```python
@app.get("/health")
def liveness():
    return {"status": "ok"}

@app.get("/health/ready")
def readiness(db: Session):
    try:
        db.execute("SELECT 1")  # Verify DB connection
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503
```

**Rationale**: Kubernetes-ready pattern; supports smart health-aware load balancing

---

## Pattern 10: Partial Audit Logging

**Requirement**: Track important decisions for compliance

**Pattern**:
```
Cost Entry: Immutable (no updates, no audit needed)
Recommendation Status: Mutable (track changes in audit table)
```

**Audit Table**:
```
id | recommendation_id | old_status | new_status | timestamp | user_id
```

**Rationale**: Cost entries are write-once (no audit table needed); status changes are rare but important to track

---

## Summary

**Design Philosophy**: Simple, secure, and scalable

- **Security**: Layered validation, safe errors, security headers
- **Performance**: Connection pooling, on-demand queries, no caching (yet)
- **Scalability**: Stateless design, read replicas ready, horizontal scaling ready
- **Reliability**: Transactional writes, health checks, graceful degradation
- **Observability**: Request IDs, structured JSON logs, basic metrics

All patterns are **production-ready** (can run as-is) while staying **demo-simple** (minimal complexity).
