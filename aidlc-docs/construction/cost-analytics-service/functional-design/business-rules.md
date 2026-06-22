# Business Rules - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: Functional Design  
**Date**: 2026-06-19

---

## Overview

This document specifies the business rules, validation logic, constraints, and decision trees that govern API behavior.

---

## Section 1: Cost Data Ingestion Rules

### Rule 1.1: Cost Amount Validation
- **Requirement**: All cost amounts must be positive decimals with exactly 2 decimal places
- **Validation**: amount > 0
- **Max Value**: No hard limit (accept $999,999.99 or larger if valid)
- **Rounding**: Round to 2 decimal places using ROUND_HALF_UP
- **Error**: Return 400 Bad Request with "amount must be a positive decimal"

### Rule 1.2: Service Name Validation
- **Requirement**: Service name is required, non-empty, alphanumeric + hyphens
- **Format**: [a-zA-Z0-9-]{1,64}
- **Validation**: Must match regex; no spaces, special characters, or wildcards
- **Flexibility**: Accept any service name (no AWS whitelist) — allows custom services and future AWS services
- **Error**: Return 400 Bad Request with "invalid service name format"

### Rule 1.3: Timestamp Validation
- **Requirement**: Timestamp is required, ISO 8601 format, in UTC, not in the future
- **Format**: YYYY-MM-DDTHH:MM:SSZ (e.g., "2026-06-19T10:30:45Z")
- **Constraint**: Must represent actual cost incurrence time (AWS billing time), not ingestion time
- **Historical Range**: No limit — accept any past date (users may backfill historical data)
- **Future Protection**: Reject if timestamp > now() (prevent pre-dated costs)
- **Error**: Return 400 Bad Request with "timestamp must be in ISO 8601 format and not in the future"

### Rule 1.4: Tag Validation
- **Requirement**: Tags are optional; when provided, must be non-empty strings
- **Format**: Each tag [a-zA-Z0-9_-]{1,64}
- **Deduplication**: If user submits ["prod", "prod"], deduplicate to ["prod"]
- **Creation**: Tags are created implicitly on first reference (lazy creation)
- **Validation**: No empty strings, no whitespace-only strings
- **Error**: Return 400 Bad Request with "tag must be non-empty string"

### Rule 1.5: Cost Entry Immutability
- **Requirement**: Cost entries cannot be modified once created
- **Operations Allowed**: Create (POST), Read (GET), Delete (DELETE)
- **Operations Forbidden**: Partial updates (PATCH)
- **Rationale**: Ensures audit trail integrity — cost data must be immutable for compliance
- **Error**: Return 405 Method Not Allowed if PATCH is attempted on /cost-data/{id}

### Rule 1.6: Duplicate Cost Handling
- **Requirement**: Allow duplicate cost entries (same service, amount, timestamp)
- **Rationale**: Ingestion systems may re-submit the same cost; deduplication is caller's responsibility
- **No Uniqueness Constraint**: Database permits duplicates
- **Implication**: Aggregations may include duplicates; callers must filter if needed

---

## Section 2: Daily Spending Trends Rules

### Rule 2.1: Daily Aggregation Algorithm
- **Aggregation Level**: Sum all cost amounts grouped by calendar date (UTC)
- **Timezone**: Always UTC (no customization)
- **Grouping**: GROUP BY DATE(timestamp) in UTC
- **Result**: One record per date per service filter
- **Precision**: Maintain decimal precision (no rounding loss during aggregation)

### Rule 2.2: Sparse Response for Trends
- **Requirement**: Return only dates with cost data (sparse response)
- **Implication**: If costs exist for June 15 and June 18, only return those 2 dates (not June 16, 17)
- **Rationale**: Cleaner response, typical for FinOps dashboards
- **Pagination**: Apply cursor-based pagination to sparse results

### Rule 2.3: Service Filtering for Trends
- **Requirement**: When service filter is applied, return aggregates for that service only
- **Example**: GET /cost-data/daily?service=EC2 returns only EC2 costs per day
- **No Filtering**: GET /cost-data/daily returns all services combined per day
- **Error**: Invalid service name format → 400 Bad Request (but accepts any service name, even if no data)

### Rule 2.4: Pagination Cursor for Trends
- **Cursor Type**: Date-based (not record-based)
- **Format**: Opaque base64-encoded date (e.g., "2026-06-10")
- **Semantics**: Cursor points to the start of the next page (date to start from)
- **Implementation**: Next cursor = last date returned + 1 day (or similar logic)
- **Metadata**: Respond with `next_cursor`, `has_more`, `items_count`
- **Edge Case**: When no more data, `has_more=false`, `next_cursor=null`

---

## Section 3: Anomaly Detection Rules

### Rule 3.1: Anomaly Detection Algorithm
- **Trigger**: Daily cost > (7-day rolling average × 1.25)
- **Baseline Calculation**: Average of cost amounts from the 7 calendar days prior
- **Detection Method**: For each date, compute baseline average, compare spike
- **Spike Percentage**: (spike_cost - baseline) / baseline × 100
- **Threshold**: 25% above baseline (immovable for this demo)

### Rule 3.2: Bootstrap Mode (Insufficient Historical Data)
- **Requirement**: If <7 days of data exist, use available data only
- **Example**: On June 3, use June 1-2 average (2 days) if no earlier data
- **Implication**: Anomalies are detected early, with lower confidence
- **Confidence Indicator**: Spike percentage still reported; high percentage may indicate real spike

### Rule 3.3: Anomaly Time Basis
- **Requirement**: Use calendar dates (not "7 most recent data points")
- **Rationale**: Cloud costs are tied to calendar days; 7 calendar days ago is more intuitive
- **Timezone**: All dates in UTC

### Rule 3.4: Multiple Anomalies per Service per Period
- **Requirement**: Report one anomaly record per date per service
- **Example**: If EC2 spikes on June 15 AND June 18, return two separate anomaly records
- **No Aggregation**: Do not merge consecutive spikes into one event
- **Rationale**: Simplifies implementation; post-processing can cluster if needed

### Rule 3.5: Anomaly Response Content
- **Return**: date, service, baseline_average, spike_cost, spike_percentage
- **Ordering**: Sort by spike_percentage descending (highest impact first)
- **Filtering**: Optional service filter (GET /cost-data/anomalies?service=EC2)
- **No Pagination**: Anomalies list is typically small; return all matching results

---

## Section 4: Optimization Recommendations Rules

### Rule 4.1: Recommendation Status Lifecycle
- **Initial Status**: "recommended"
- **One-Way Transitions**: 
  - recommended → implemented (user took action)
  - recommended → dismissed (user decided to skip)
  - No reversions (dismissed cannot go back to recommended)
- **Rationale**: Immutable audit trail; if dismissed item becomes relevant again, create new recommendation

### Rule 4.2: Recommendation Read-Only in API
- **Requirement**: API does not create or modify recommendation details; only status updates allowed
- **Details Immutable**: title, description, estimated_monthly_savings, service cannot be changed
- **Status Update Only**: PATCH /optimization/{id} with {"status": "implemented"} is allowed
- **Rationale**: Keeps API focused on FinOps tracking; recommendation generation is external process
- **Error**: Attempt to PATCH other fields → 400 Bad Request

### Rule 4.3: Recommendation Status Validation
- **Valid Statuses**: "recommended", "implemented", "dismissed"
- **Case-Sensitive**: "Implemented" or "IMPLEMENTED" are invalid
- **Validation**: Reject invalid status values with 400 Bad Request
- **Error Message**: "status must be one of: recommended, implemented, dismissed"

### Rule 4.4: Recommendation Filtering and Sorting
- **Filtering**: Support optional service and status filters
  - GET /optimization/recommendations?service=EC2&status=recommended
- **Sorting**: By estimated_monthly_savings (descending) — highest impact first
- **Pagination**: Cursor-based, default 20, max 100 (same as trends)

### Rule 4.5: Recommendation Permanence
- **No Expiration**: Recommendations never expire or auto-delete
- **No Soft Delete**: Dismissed recommendations remain queryable (filter by status if needed)
- **Audit Trail**: Full history of all recommendations maintained forever

---

## Section 5: Error Handling Rules

### Rule 5.1: HTTP Status Codes
| Scenario | Status | Example Message |
|----------|--------|-----------------|
| Invalid input (format, validation) | 400 | "amount must be a positive decimal" |
| Resource not found | 404 | "recommendation with id {id} not found" |
| Method not allowed | 405 | "PATCH is not allowed on /cost-data/{id}" |
| Successful GET/PATCH/DELETE | 200 | (no message body) |
| Successful POST | 201 | (response body includes created resource) |
| DELETE successful | 204 | (empty response body) |
| Server error | 500 | "Internal server error" (no stack trace) |

### Rule 5.2: Error Response Format
- **Structure**: {"error": "human-readable message"}
- **No Error Codes**: Do not expose internal error codes (e.g., "ERR_INVALID_AMOUNT")
- **No Stack Traces**: Never include stack traces in production responses
- **Security**: Avoid exposing internal database details
- **Example**: 
  ```json
  {
    "error": "amount must be a positive decimal"
  }
  ```

### Rule 5.3: Missing/Null Handling
- **Null Required Fields**: Return 400 Bad Request
- **Missing Optional Fields**: Treat as empty (e.g., tags = [])
- **Empty Strings**: For required string fields, treat as missing

### Rule 5.4: Concurrent Write Handling
- **Multiple Simultaneous POST /cost-data**: Accept all (SQLite ACID handles concurrency)
- **No Locking**: Do not use pessimistic locking or idempotency keys
- **Duplicates Allowed**: Multiple callers can submit same cost entry
- **Outcome**: All writes succeed if valid

---

## Section 6: Data Consistency Rules

### Rule 6.1: Timestamp Consistency
- **Ingestion Time vs. Cost Time**: 
  - `timestamp` = when cost was incurred (user-provided)
  - `created_at` = when entry was ingested (server-generated)
- **Implication**: Cost from June 1 can be ingested on June 10 (historical backfill)

### Rule 6.2: Tag Consistency
- **Implicit Creation**: Tags are created automatically on first reference in any cost entry
- **Global Registry**: Once created, tag exists for all future queries
- **No Orphans**: Tags without associated costs still exist (permanent)

### Rule 6.3: Aggregation Consistency
- **No Rounding Loss**: Aggregations maintain decimal precision (sum of decimals)
- **Query Reproducibility**: Same query at different times returns same numerical totals (assuming no new costs added)

---

## Summary

These rules are designed to be:
- **Simple and auditable** — easy to trace decisions in code and tests
- **FinOps-aligned** — immutable costs, status tracking, clear anomaly thresholds
- **API-idiomatic** — standard HTTP semantics, clear error handling
- **Testable** — each rule can be verified via example-based and property-based tests
