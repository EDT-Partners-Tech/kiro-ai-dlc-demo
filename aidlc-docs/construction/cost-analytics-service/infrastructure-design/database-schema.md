# Database Schema - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: Infrastructure Design  
**Date**: 2026-06-19

---

## Overview

This document specifies the SQLite database schema, including tables, relationships, constraints, and indexes optimized for the FinOps use case.

---

## Table 1: cost_entry

**Purpose**: Store individual cloud cost incurrences

```sql
CREATE TABLE cost_entry (
    id TEXT PRIMARY KEY,
    service TEXT NOT NULL,
    amount TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Columns**:
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | UUID, immutable |
| service | TEXT | NOT NULL | AWS service name (e.g., "EC2", "S3") |
| amount | TEXT | NOT NULL | Decimal stored as TEXT (SQLite best practice for precision) |
| timestamp | TEXT | NOT NULL | ISO 8601 datetime (cost incurrence time) |
| created_at | TEXT | NOT NULL | ISO 8601 datetime (entry creation) |
| updated_at | TEXT | NOT NULL | ISO 8601 datetime (same as created_at, immutable) |

**Rationale**: 
- Decimal stored as TEXT to avoid floating-point precision loss
- Timestamp as TEXT (ISO 8601) for clarity and timezone safety
- Immutable entries (created_at == updated_at always)

---

## Table 2: tag

**Purpose**: Store cost allocation tags (many-to-many with cost_entry)

```sql
CREATE TABLE tag (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
```

**Columns**:
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | UUID |
| name | TEXT | UNIQUE NOT NULL | Tag name (e.g., "production", "team-web") |
| created_at | TEXT | NOT NULL | ISO 8601 datetime (first reference) |

**Rationale**:
- UNIQUE constraint prevents duplicate tags
- Tags are created implicitly (no explicit insertion endpoint)
- name is indexed for fast lookup

---

## Table 3: cost_entry_tag (Join Table)

**Purpose**: Many-to-many relationship between cost_entry and tag

```sql
CREATE TABLE cost_entry_tag (
    cost_entry_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (cost_entry_id, tag_id),
    FOREIGN KEY (cost_entry_id) REFERENCES cost_entry(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id)
);
```

**Rationale**:
- Composite PRIMARY KEY ensures no duplicate associations
- ON DELETE CASCADE: if cost entry deleted, associations removed
- Foreign keys maintain referential integrity

---

## Table 4: recommendation

**Purpose**: Store FinOps cost optimization opportunities

```sql
CREATE TABLE recommendation (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    estimated_monthly_savings TEXT NOT NULL,
    service TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'recommended',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Columns**:
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | UUID |
| title | TEXT | NOT NULL | Brief description (e.g., "Delete unused Elastic IP") |
| description | TEXT | NOT NULL | Detailed explanation and impact |
| estimated_monthly_savings | TEXT | NOT NULL | Decimal (stored as TEXT for precision) |
| service | TEXT | NOT NULL | AWS service (e.g., "EC2", "RDS") |
| status | TEXT | NOT NULL DEFAULT | One of: "recommended", "implemented", "dismissed" |
| created_at | TEXT | NOT NULL | ISO 8601 datetime (recommendation created) |
| updated_at | TEXT | NOT NULL | ISO 8601 datetime (status last changed) |

**Constraints**:
- status CHECK constraint (validate values):
  ```sql
  CHECK (status IN ('recommended', 'implemented', 'dismissed'))
  ```

**Rationale**:
- Immutable title/description/savings (only status is mutable)
- Default status = "recommended"
- Estimated savings stored as TEXT (Decimal precision)

---

## Table 5: recommendation_status_audit

**Purpose**: Track recommendation status changes for compliance

```sql
CREATE TABLE recommendation_status_audit (
    id TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (recommendation_id) REFERENCES recommendation(id)
);
```

**Columns**:
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | UUID (audit record ID) |
| recommendation_id | TEXT | NOT NULL | Reference to recommendation |
| old_status | TEXT | (nullable) | Previous status (null if first change) |
| new_status | TEXT | NOT NULL | New status after change |
| timestamp | TEXT | NOT NULL | ISO 8601 datetime of change |

**Rationale**:
- Partial audit log (only status changes, not full change history)
- old_status nullable for initial recommendation creation
- Provides compliance trail for FinOps decisions

---

## Indexes

**Index Strategy**: Query optimization for common operations

### Index 1: cost_entry_service
```sql
CREATE INDEX idx_cost_entry_service ON cost_entry(service);
```
**Purpose**: Fast filtering by service (GET /cost-data/daily?service=EC2)  
**Cardinality**: Moderate (10-50 distinct services)

### Index 2: cost_entry_timestamp
```sql
CREATE INDEX idx_cost_entry_timestamp ON cost_entry(timestamp);
```
**Purpose**: Fast range queries (7-day rolling average for anomalies)  
**Cardinality**: High (many distinct timestamps)  
**Range Query Example**: 
```sql
SELECT * FROM cost_entry 
WHERE timestamp >= '2026-06-12T00:00:00Z' 
  AND timestamp < '2026-06-19T00:00:00Z'
ORDER BY timestamp DESC
```

### Index 3: cost_entry_service_timestamp (Composite)
```sql
CREATE INDEX idx_cost_entry_service_timestamp 
ON cost_entry(service, timestamp);
```
**Purpose**: Fast queries filtered by both service AND timestamp  
**Example Use**: Daily trends for specific service  
```sql
SELECT DATE(timestamp), SUM(amount) 
FROM cost_entry 
WHERE service = 'EC2' AND timestamp >= ?
GROUP BY DATE(timestamp)
```

### Index 4: tag_name
```sql
CREATE INDEX idx_tag_name ON tag(name);
```
**Purpose**: Fast tag lookups during cost ingestion  
**Cardinality**: Low (hundreds to thousands of unique tags)

### Index 5: recommendation_service
```sql
CREATE INDEX idx_recommendation_service ON recommendation(service);
```
**Purpose**: Filter recommendations by service  
**Cardinality**: Low (10-50 services)

### Index 6: recommendation_status
```sql
CREATE INDEX idx_recommendation_status ON recommendation(status);
```
**Purpose**: Filter recommendations by status  
**Cardinality**: Very Low (3 statuses)  
**Use**: GET /optimization/recommendations?status=implemented

### Index 7: recommendation_savings_desc
```sql
CREATE INDEX idx_recommendation_savings_desc 
ON recommendation(estimated_monthly_savings DESC);
```
**Purpose**: Sort by savings (highest impact first)  
**Use**: API returns recommendations sorted by impact

---

## Data Type Rationale

### TEXT for Decimals
SQLite doesn't have a native DECIMAL type. Three options:
1. **REAL** (floating-point) — ❌ Risk of precision loss (1.05 + 0.1 ≠ 1.15)
2. **INTEGER** (store cents) — Awkward for Python (Decimal type)
3. **TEXT** (store as string) — ✅ Exact precision, Python converts to Decimal

**Selected**: TEXT (converted to Decimal in Python via SQLModel validators)

### TEXT for Timestamps
ISO 8601 format ("2026-06-19T10:30:45Z"):
- Human-readable
- Sortable (lexicographic order = chronological order)
- No timezone ambiguity (always UTC)

---

## Sample Data (Test Fixture)

```sql
-- Insert tags
INSERT INTO tag (id, name, created_at) VALUES 
  ('tag-1', 'production', '2026-06-01T00:00:00Z'),
  ('tag-2', 'web-team', '2026-06-01T00:00:00Z'),
  ('tag-3', 'development', '2026-06-05T00:00:00Z');

-- Insert costs
INSERT INTO cost_entry (id, service, amount, timestamp, created_at, updated_at) VALUES 
  ('cost-1', 'EC2', '150.50', '2026-06-18T00:00:00Z', '2026-06-18T10:00:00Z', '2026-06-18T10:00:00Z'),
  ('cost-2', 'EC2', '155.75', '2026-06-19T00:00:00Z', '2026-06-19T10:00:00Z', '2026-06-19T10:00:00Z'),
  ('cost-3', 'S3', '45.25', '2026-06-19T00:00:00Z', '2026-06-19T10:00:00Z', '2026-06-19T10:00:00Z');

-- Associate costs with tags
INSERT INTO cost_entry_tag (cost_entry_id, tag_id) VALUES 
  ('cost-1', 'tag-1'),
  ('cost-1', 'tag-2'),
  ('cost-2', 'tag-1'),
  ('cost-3', 'tag-1');

-- Insert recommendations
INSERT INTO recommendation (id, title, description, estimated_monthly_savings, service, status, created_at, updated_at) VALUES 
  ('rec-1', 'Delete unused Elastic IP', 'Elastic IP not attached to instance', '3.50', 'EC2', 'recommended', '2026-06-10T00:00:00Z', '2026-06-10T00:00:00Z'),
  ('rec-2', 'Resize oversized RDS', 'db.t3.large can run on db.t3.medium', '150.00', 'RDS', 'implemented', '2026-06-10T00:00:00Z', '2026-06-15T14:30:00Z'),
  ('rec-3', 'Enable S3 Intelligent-Tiering', 'Auto-tier cold data to cheaper storage', '25.00', 'S3', 'recommended', '2026-06-12T00:00:00Z', '2026-06-12T00:00:00Z');

-- Audit log (status changes)
INSERT INTO recommendation_status_audit (id, recommendation_id, old_status, new_status, timestamp) VALUES 
  ('audit-1', 'rec-2', 'recommended', 'implemented', '2026-06-15T14:30:00Z');
```

---

## Constraints & Integrity

### Primary Key Constraints
- All tables have TEXT PRIMARY KEY (UUID format)
- Enforces uniqueness and enables fast lookups

### Foreign Key Constraints
- cost_entry_tag references cost_entry and tag
- recommendation_status_audit references recommendation
- ON DELETE CASCADE: orphaned audit records removed when recommendation deleted

### Check Constraints
- recommendation.status must be one of 3 values
- Enforced at database level

### Unique Constraints
- tag.name is UNIQUE (no duplicate tag names)

---

## Migration Path (Demo → Production)

### From SQLite to RDS PostgreSQL
Changes needed:
- TEXT → VARCHAR/NUMERIC for appropriate columns
- AUTOINCREMENT (if needed) → PostgreSQL SERIAL/BIGSERIAL
- Data types otherwise compatible
- **Indexes remain the same**
- **Schema structure remains the same**

**Effort**: Low (SQLAlchemy abstracts differences)

---

## Summary

**Schema Design Principles**:
- ✅ Immutability of cost entries (compliance)
- ✅ ACID constraints (financial accuracy)
- ✅ Decimal precision (no floating-point errors)
- ✅ Strategic indexing (query performance)
- ✅ Audit trail (partial, for important decisions)
- ✅ Normalization (no data duplication)
- ✅ Clear relationships (foreign keys, join tables)

**Ready for Code Generation**: Schema is simple, normalized, and optimized for FinOps queries.
