# Domain Entities - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: Functional Design  
**Date**: 2026-06-19

---

## Overview

This document defines the core domain entities, their attributes, relationships, and business semantics.

---

## Entity 1: CostEntry

**Purpose**: Represents a single cloud cost incurred during a specific timestamp.

**Attributes**:
| Attribute | Type | Required | Auto-Generated | Description |
|-----------|------|----------|-----------------|-------------|
| id | UUID | Yes | Yes | Unique identifier |
| service | String | Yes | No | AWS service name (e.g., "EC2", "S3", "Lambda") — alphanumeric + hyphens |
| amount | Decimal | Yes | No | Cost in USD with 2 decimal places. Must be > 0 |
| timestamp | ISO 8601 DateTime | Yes | No | When the cost was incurred (not when ingested). Must be ≤ today (no future dates) |
| tags | List[String] | No | No | Associated cost allocation tags (many-to-many via Tag entity) |
| created_at | ISO 8601 DateTime | Yes | Yes | Server timestamp when entry was created |
| updated_at | ISO 8601 DateTime | Yes | Yes | Server timestamp of last modification (initially = created_at, never changes for CostEntry) |

**Business Rules**:
- Service name must be alphanumeric + hyphens (no spaces, special chars)
- Amount must be a positive decimal with max 2 decimal places
- Timestamp must be a valid ISO 8601 datetime in UTC, not in the future
- Cost entries are **immutable once created** — only deletion is allowed (no updates)
- Tags are created implicitly when referenced; duplicates are automatically deduplicated
- Duplicate cost entries (same service, amount, timestamp) are **allowed** — deduplication is caller's responsibility

**Relationships**:
- Many-to-Many with Tag (via join table)

---

## Entity 2: Tag

**Purpose**: Represents a cost allocation tag used to organize costs by business dimension.

**Attributes**:
| Attribute | Type | Required | Auto-Generated | Description |
|-----------|------|----------|-----------------|-------------|
| id | UUID | Yes | Yes | Unique identifier |
| name | String | Yes | No | Tag name (e.g., "production", "team-web"). Must be non-empty, alphanumeric + hyphens/underscores |
| created_at | ISO 8601 DateTime | Yes | Yes | Server timestamp when tag was first used |

**Business Rules**:
- Tag name must be non-empty, alphanumeric + hyphens/underscores (allow user naming conventions like "team-web", "env_prod")
- Tags are created implicitly on first reference (lazy creation)
- No explicit tag deletion — tags exist forever (even if no associated costs)
- Tag names are case-sensitive

**Relationships**:
- Many-to-Many with CostEntry (via join table)

---

## Entity 3: Recommendation

**Purpose**: Represents a FinOps optimization opportunity with status tracking.

**Attributes**:
| Attribute | Type | Required | Auto-Generated | Description |
|-----------|------|----------|-----------------|-------------|
| id | UUID | Yes | Yes | Unique identifier |
| title | String | Yes | No | Brief description (e.g., "Delete unused Elastic IP") |
| description | String | Yes | No | Detailed explanation and impact assessment |
| estimated_monthly_savings | Decimal | Yes | No | Projected savings in USD, 2 decimal places, > 0 |
| service | String | Yes | No | AWS service this applies to (e.g., "EC2", "RDS") |
| status | Enum | Yes | No | One of: "recommended" (default), "implemented", "dismissed" |
| created_at | ISO 8601 DateTime | Yes | Yes | Server timestamp when recommendation was created |
| updated_at | ISO 8601 DateTime | Yes | Yes | Server timestamp of last status change |

**Business Rules**:
- Recommendations are **read-only in this API** — created externally (pre-populated)
- Status transitions are **one-way**: recommended → (implemented OR dismissed). Cannot revert
- Updated_at tracks when status was last changed
- Estimated savings must be positive and realistic (no validation on reasonableness)
- Service name follows same rules as CostEntry (alphanumeric + hyphens)

**Relationships**:
- None (recommendations are independent entities)

---

## Entity 4: DailyCostAggregate (Derived/Query Result)

**Purpose**: Represents a daily cost aggregation (derived entity, not persisted).

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| date | ISO 8601 Date (YYYY-MM-DD) | Yes | The calendar date in UTC |
| total_cost | Decimal | Yes | Sum of all costs for that date |
| service | String | No | If filtered by service, the service name; otherwise null (represents all services) |
| cost_count | Integer | Yes | Number of individual cost entries for this day |

**Business Rules**:
- Aggregated in UTC timezone only (no timezone customization)
- Sum is performed at database level (not in-memory) for accuracy
- If service filter is applied, only includes costs for that service
- Only days with at least one cost entry are returned (sparse response)
- Used for trending queries and reporting

**Relationships**:
- Derived from CostEntry (read-only view)

---

## Entity 5: AnomalyDetectionResult (Derived/Query Result)

**Purpose**: Represents a detected spending anomaly (derived entity, not persisted).

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| date | ISO 8601 Date | Yes | The date when the anomaly occurred |
| service | String | Yes | The service with anomalous spending |
| baseline_average | Decimal | Yes | 7-day rolling average (or less if <7 days data) |
| spike_cost | Decimal | Yes | Actual cost on the anomaly date |
| spike_percentage | Decimal | Yes | Percentage above baseline (e.g., 25.50 for 25.5% above) |

**Business Rules**:
- Anomalies are detected when daily cost > baseline average × 1.25 (25% above)
- Baseline is computed from the **7 calendar days prior** to the anomaly date
- If <7 days of historical data exist, use available data only (bootstrap mode)
- One anomaly record per day per service (separate records for June 15 and June 18)
- Includes both baseline and spike for transparency (allows clients to compute confidence)
- Returned in descending order by spike_percentage (highest impact first)

**Relationships**:
- Derived from CostEntry (read-only analysis result)

---

## Relationship Diagram (Text)

```
CostEntry (many) ──── (many) Tag
  │                              │
  │                              │
  └──── DailyCostAggregate       │
  │      (derived query)         │
  │                              │
  └──── AnomalyDetectionResult   │
         (derived analysis)      │
                                 │
Recommendation                   │
  (independent)                  │
```

---

## Data Type Specifications

### Decimal (Monetary Amounts)
- Precision: `DECIMAL(10, 2)` — up to $9,999,999.99
- Python representation: `Decimal` from `decimal` module (NOT float)
- Rounding mode: `ROUND_HALF_UP` for consistency
- Validation: Amount > 0, always 2 decimal places in responses

### String (Service Names, Tags)
- Max length: 64 characters
- Allowed characters: a-z, A-Z, 0-9, hyphen (-), underscore (_)
- Case-sensitive
- No leading/trailing whitespace

### DateTime
- Format: ISO 8601 (e.g., "2026-06-19T10:30:45Z")
- Timezone: UTC only (always ends with 'Z')
- Storage: Stored in UTC, returned in UTC
- Validation: No future dates for cost timestamps

---

## Summary

The domain model is intentionally simple to showcase AI-DLC decision-making:
- **Immutable costs** demonstrate audit trail importance (delete-only, not update)
- **One-way status transitions** show business rule modeling
- **Derived entities** (DailyCostAggregate, AnomalyDetectionResult) separate queries from persistence
- **Decimal type** enforces financial accuracy without floating-point errors
- All design decisions are **documented in audit trail**, making the reasoning transparent
