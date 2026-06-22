# Logical Components - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: NFR Design  
**Date**: 2026-06-19

---

## Overview

This document describes the logical components and their interactions to support non-functional requirements (performance, scalability, reliability, security).

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  Security Middleware                                          │
│  ├─ Request ID generation                                    │
│  ├─ Security headers injection                               │
│  └─ Error handler (catches all exceptions)                   │
├─────────────────────────────────────────────────────────────┤
│  API Endpoints (6 routes)                                    │
│  ├─ POST   /cost-data                                        │
│  ├─ GET    /cost-data/daily                                  │
│  ├─ GET    /cost-data/anomalies                              │
│  ├─ GET    /optimization/recommendations                     │
│  ├─ PATCH  /optimization/{id}                                │
│  ├─ DELETE /cost-data/{id}                                   │
│  ├─ GET    /health                                           │
│  └─ GET    /health/ready                                     │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer (validation, aggregation, anomalies)   │
├─────────────────────────────────────────────────────────────┤
│  Data Access Layer (SQLAlchemy/SQLModel ORM)                 │
│  ├─ Connection Pool (size=5, max=20)                         │
│  └─ Query builders (for trends, anomalies, etc.)             │
├─────────────────────────────────────────────────────────────┤
│                    SQLite Database                            │
│  ├─ cost_entry table + indexes                               │
│  ├─ tag table + indexes                                      │
│  ├─ cost_entry_tag join table                                │
│  ├─ recommendation table + indexes                           │
│  └─ recommendation_status_audit table                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Component 1: Security Middleware

**Responsibility**: Validate requests, add security headers, handle errors

**Features**:
- Request ID generation (UUID per request)
- Security header injection (X-Frame-Options, X-Content-Type-Options)
- Global exception handler (catches all unhandled exceptions)
- Error mapping (exception → HTTP status + safe message)

**Inputs**:
- HTTP request (any endpoint)

**Outputs**:
- HTTP response with security headers
- X-Request-ID header (for tracing)
- Structured JSON error response (if error)

**Rationale**: Single point for cross-cutting security concerns

---

## Component 2: Input Validation Layer

**Responsibility**: Validate request data before processing

**Layers**:
1. **Pydantic Models** (FastAPI auto-validates)
   - Type checking (service: str, amount: Decimal)
   - Required field checking
   - Custom validators for business rules

2. **Middleware / Business Logic** (custom validation)
   - Amount > 0
   - Timestamp not in future
   - Service name alphanumeric + hyphens

**Failure Mode**: Return 400 Bad Request with error message

**Rationale**: Fail fast, prevent invalid data from reaching database

---

## Component 3: API Endpoints

**Responsibility**: Handle HTTP requests and route to business logic

**Endpoints**:

| Endpoint | Method | Validates | Returns |
|----------|--------|-----------|---------|
| /cost-data | POST | CostEntry | Created entry (201) or error (400) |
| /cost-data/daily | GET | Filters, pagination | Daily aggregates (200) or error |
| /cost-data/anomalies | GET | Service filter | Anomalies (200) or error |
| /optimization/recommendations | GET | Filters, pagination | Recommendations (200) or error |
| /optimization/{id} | PATCH | Status update | Updated recommendation (200) or error (404) |
| /cost-data/{id} | DELETE | ID exists | 204 No Content or 404 |
| /health | GET | (none) | {"status": "ok"} (200) |
| /health/ready | GET | DB connectivity | {"status": "ready"} (200/503) |

**Rationale**: Clear separation of concerns; each endpoint handles one business operation

---

## Component 4: Business Logic Layer

**Responsibility**: Implement core FinOps algorithms and rules

**Subcomponents**:

### 4a: Cost Ingestion Logic
- Validate inputs (amount, service, timestamp)
- Create or reference tags
- Persist to database (transactional)

### 4b: Daily Aggregation Logic
- Query costs for given date range and service filter
- Group by date, sum amounts
- Return sparse results (only dates with data)

### 4c: Anomaly Detection Logic
- Fetch 7-day baseline data
- Compute average cost per day
- Compare current day to baseline
- Flag if > 25% above baseline
- Return spike percentage for transparency

### 4d: Recommendation Management Logic
- Query recommendations with filters (service, status)
- Sort by estimated savings
- Handle status transitions (recommended → implemented/dismissed)
- Prevent invalid transitions

**Rationale**: Business logic is independent of framework; easy to test and reuse

---

## Component 5: Data Access Layer (ORM)

**Responsibility**: Translate between objects (Python) and database (SQL)

**Technology**: SQLAlchemy + SQLModel

**Features**:
- Connection pooling (min=5, max=20)
- Query builders (type-safe, prevent SQL injection)
- Transaction management (automatic per FastAPI request)
- Relationship management (CostEntry ↔ Tag many-to-many)

**Inputs**:
- Business logic queries (high-level)

**Outputs**:
- Database results (ORM objects)

**Rationale**: ORM abstracts SQL; enables database migration (SQLite → RDS) without code changes

---

## Component 6: SQLite Database

**Responsibility**: Store and query data persistently

**Schema**:

### Table: cost_entry
```sql
CREATE TABLE cost_entry (
    id UUID PRIMARY KEY,
    service VARCHAR(64) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW()
);
CREATE INDEX idx_cost_entry_service ON cost_entry(service);
CREATE INDEX idx_cost_entry_timestamp ON cost_entry(timestamp);
```

### Table: tag
```sql
CREATE TABLE tag (
    id UUID PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT NOW()
);
```

### Table: cost_entry_tag (many-to-many join)
```sql
CREATE TABLE cost_entry_tag (
    cost_entry_id UUID,
    tag_id UUID,
    PRIMARY KEY (cost_entry_id, tag_id),
    FOREIGN KEY (cost_entry_id) REFERENCES cost_entry(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id)
);
```

### Table: recommendation
```sql
CREATE TABLE recommendation (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    estimated_monthly_savings DECIMAL(10,2) NOT NULL,
    service VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'recommended',
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW()
);
CREATE INDEX idx_recommendation_service ON recommendation(service);
CREATE INDEX idx_recommendation_status ON recommendation(status);
CREATE INDEX idx_recommendation_savings ON recommendation(estimated_monthly_savings DESC);
```

### Table: recommendation_status_audit (partial audit log)
```sql
CREATE TABLE recommendation_status_audit (
    id UUID PRIMARY KEY,
    recommendation_id UUID,
    old_status VARCHAR(32),
    new_status VARCHAR(32),
    timestamp DATETIME DEFAULT NOW(),
    FOREIGN KEY (recommendation_id) REFERENCES recommendation(id)
);
```

**Rationale**: Indexes on frequently-queried columns (service, timestamp, status); audit table for compliance

---

## Component 7: Observability (Logging & Metrics)

**Responsibility**: Emit operational signals for debugging and monitoring

**Signals**:

### Request Logging
```json
{
  "timestamp": "2026-06-19T10:30:45Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/cost-data",
  "status": 201,
  "latency_ms": 45,
  "service": "EC2"
}
```

### Error Logging
```json
{
  "timestamp": "2026-06-19T10:30:46Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "method": "POST",
  "path": "/cost-data",
  "status": 400,
  "error": "amount must be positive",
  "detail": "Validation error for CostEntry.amount"
}
```

### Metrics
- Request count per endpoint
- Latency histogram (p50, p90, p99)
- Error count per status code

**Rationale**: JSON logs are structured and searchable; metrics enable performance monitoring

---

## Component 8: Health Checks

**Responsibility**: Signal API liveness and readiness

**Liveness** (GET /health):
- Always returns 200 OK
- Signals: "Process is running"
- Used for: Container health, uptime monitoring

**Readiness** (GET /health/ready):
- Verifies database connectivity
- Returns 503 if database unavailable
- Signals: "Ready to serve requests"
- Used for: Kubernetes readiness probes, load balancer drain

**Rationale**: Enables smart load balancing; prevents traffic routing to unhealthy instances

---

## Component 9: Connection Pool

**Responsibility**: Manage database connections efficiently

**Configuration**:
- Minimum connections: 5 (always maintained)
- Maximum connections: 20 (total including overflow)
- Pool pre-ping: True (verify connection before use)

**Benefits**:
- Connection reuse (avoid creation overhead)
- Resource limits (bounded connections)
- Stale connection detection (pre-ping)

**Rationale**: Standard practice; minimal overhead; critical for production scale

---

## Component Interactions (Happy Path Example)

**Scenario**: User ingests a cost entry

```
1. Request arrives at Security Middleware
   └─ Generate request_id: "abc-123"
   └─ Add to context (for logging)

2. Validation Middleware
   └─ Pydantic parses JSON → CostEntry model
   └─ Validates types, required fields
   └─ Calls business logic if valid

3. Business Logic: Cost Ingestion
   └─ Check amount > 0
   └─ Check timestamp not in future
   └─ Check service format
   └─ Create Tag entities (if new)
   └─ Start database transaction

4. Data Access Layer
   └─ Query tag table (or create new)
   └─ Insert cost_entry row
   └─ Insert cost_entry_tag join rows
   └─ Commit transaction

5. Database (SQLite)
   └─ ACID guarantee: all-or-nothing

6. Response
   └─ Return created entry (201 Created)
   └─ Include X-Request-ID header

7. Observability
   └─ Log: method=POST, path=/cost-data, status=201, latency=45ms
```

---

## Summary

**Logical components are designed for**:
- **Security**: Layered validation, safe errors, security headers
- **Performance**: Connection pooling, indexed queries, on-demand aggregation
- **Scalability**: Stateless APIs, ORM abstracts database, ready for horizontal scaling
- **Reliability**: Transactional writes, health checks, graceful degradation
- **Observability**: Request IDs, structured JSON logs, health endpoints

All components follow **single responsibility principle**: each component has one clear job, making the system easy to understand and modify.
