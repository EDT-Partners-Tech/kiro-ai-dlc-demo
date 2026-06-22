# CloudSpend Analytics API - Requirements Document

## Intent Analysis

### User Request
Build a minimal REST API for cloud cost analytics and FinOps optimization using FastAPI and SQLite (SQLModel). The API should expose five core operations: cost data ingestion, daily spending trends, anomaly detection, optimization recommendations, and recommendation tracking (mark as implemented/dismissed).

### Request Type
New Project (Greenfield) - Building a new REST API application from scratch

### Scope Estimate
Single Component - REST API service with financial data persistence and analytics

### Complexity Estimate
Moderate - Multiple operations with cost calculations, anomaly detection, and FinOps reporting

### Extensions Enabled
- **Security Baseline**: Yes (production-grade security enforcement for financial data)
- **Property-Based Testing**: Yes (cost calculations and anomaly detection must be verified)

---

## Functional Requirements

### FR-1: Cost Entry Data Model
The API must manage cloud cost entries with the following attributes:
- **id**: Unique identifier (auto-generated)
- **service**: AWS service name (e.g., EC2, S3, Lambda) - required
- **amount**: Cost amount in USD (required, positive decimal)
- **timestamp**: When this cost was incurred (ISO 8601 format, required)
- **tags**: List of associated tags for cost allocation (optional, many-to-many)
- **created_at**: Timestamp of entry creation (auto-generated)
- **updated_at**: Timestamp of last update (auto-generated)

### FR-2: Optimization Recommendation Data Model
The API must manage cost optimization opportunities with:
- **id**: Unique identifier (auto-generated)
- **title**: Brief description of the opportunity (required)
- **description**: Detailed explanation and impact assessment (required)
- **estimated_monthly_savings**: Projected savings in USD (required, positive decimal)
- **service**: AWS service this recommendation applies to (required)
- **status**: Current status - "recommended" | "implemented" | "dismissed" (required, default: "recommended")
- **created_at**: Timestamp of creation (auto-generated)
- **updated_at**: Timestamp of last update (auto-generated)

### FR-3: Core Operations

#### FR-3.1: Cost Data Ingestion (POST /cost-data)
- Accept cost data (service, amount, timestamp, optional tags)
- Validate input (required fields, positive amount, valid timestamp)
- Create new cost entry with auto-generated id, created_at, updated_at
- Return created entry with full details and HTTP 201 Created

#### FR-3.2: Daily Spending Trends (GET /cost-data/daily)
- Return paginated list of daily cost aggregations (sum of costs per day)
- **Pagination Strategy**: Cursor-based pagination
- **Default Page Size**: 20
- **Maximum Page Size**: 100
- **Filtering**: Support filtering by a single service name
- **Response Metadata**: Include pagination info (next cursor, has_more)
- Return HTTP 200 OK with paginated results

#### FR-3.3: Anomaly Detection (GET /cost-data/anomalies)
- Detect and return unusual spending spikes
- **Algorithm**: Compare daily spending to 7-day rolling average; flag if > 25% above average
- **Response**: List of detected anomalies with service, date, spike amount, and baseline
- **Filtering**: Optional service name filter
- Return HTTP 200 OK with anomaly list

#### FR-3.4: Optimization Recommendations (GET /optimization/recommendations)
- Return list of cost optimization opportunities
- **Filtering**: Optional service name filter, optional status filter
- **Sorting**: By estimated_monthly_savings (descending)
- **Pagination**: Cursor-based, default 20, max 100
- Return HTTP 200 OK with paginated recommendations

#### FR-3.5: Update Recommendation Status (PATCH /optimization/{id})
- Accept status update (mark as "implemented" or "dismissed")
- Validate recommendation exists
- Update specified fields and auto-update updated_at
- Return updated recommendation or HTTP 404 if not found
- Return HTTP 200 OK on success

#### FR-3.6: Delete Cost Entry (DELETE /cost-data/{id})
- Delete a cost entry by ID
- Return HTTP 204 No Content on success
- Return HTTP 404 Not Found if entry doesn't exist

### FR-4: Tag Management
- Tags are associated with cost entries in a many-to-many relationship
- Tags are created implicitly when referenced in cost data creation/update
- Tags should be stored separately from cost entries for reusability
- Common tags: "production", "development", "staging", "web-team", "data-team", etc.

---

## Non-Functional Requirements

### NFR-1: Error Handling
- **Strategy**: Standard REST error handling with detailed error messages
- **HTTP Status Codes**:
  - 200 OK - Successful GET/PATCH
  - 201 Created - Successful POST
  - 204 No Content - Successful DELETE
  - 400 Bad Request - Invalid input (e.g., negative cost amount, invalid timestamp)
  - 404 Not Found - Resource not found
  - 500 Internal Server Error - Unhandled server errors
- **Error Response Format**: Include error message, optional error details
- **Financial Data**: No stack traces or internal system details in production error responses

### NFR-2: Data Persistence
- SQLite database with SQLModel ORM
- Database should be file-based in the workspace directory (`cloudspend.db`)
- Support concurrent read access
- Cost data is permanent and immutable once created (deletions are explicit operations)

### NFR-3: Performance
- Anomaly detection queries optimized to avoid N+1 queries
- Daily aggregation should use database-level grouping (not in-memory)
- Response time target: <500ms for list operations (at typical scale)
- Cost calculations performed server-side with proper decimal precision

### NFR-4: API Response Format
- JSON format for all responses
- **Response Metadata**: 
  - For list responses: include cursor, has_more, items_count fields
  - No timestamps or API version in responses (minimal metadata)
- Monetary amounts always as decimals with 2 decimal places

### NFR-5: Validation
- **Input Validation**:
  - Service name: Required, non-empty string, alphanumeric + hyphens
  - Amount: Required, positive decimal (> 0), max 2 decimal places
  - Timestamp: Required, valid ISO 8601 format, not in future
  - Status: Must be one of "recommended", "implemented", "dismissed"
  - Tags: Optional list of non-empty strings
- **Calculation Validation**: Cost calculations verified with property-based testing
- All validation performed server-side

### NFR-6: Security (Financial Data Protection)
- **Financial Data Classification**: All cost data is sensitive
- HTTP security headers enforced (Content-Security-Policy, X-Frame-Options, etc.)
- No hardcoded credentials or secrets
- Safe error handling (no internal database details exposed)
- Input sanitization for service names and tags
- Rate limiting recommended for production deployment (not in scope for this demo)

### NFR-7: Framework and Stack
- **Web Framework**: FastAPI
- **ORM**: SQLModel
- **Database**: SQLite
- **Language**: Python 3.11
- **Deployment**: Standalone Python process
- **Cost Precision**: Decimal type (not float) for all monetary calculations

---

## API Endpoint Summary

| Operation | Method | Path | Input | Output | Status |
|-----------|--------|------|-------|--------|--------|
| Ingest Cost | POST | /cost-data | CostEntry (service, amount, timestamp, tags) | Created CostEntry | 201/400 |
| Daily Trends | GET | /cost-data/daily?service=&cursor= | Service (optional), cursor (optional) | Paginated daily aggregations | 200 |
| Anomalies | GET | /cost-data/anomalies?service= | Service (optional) | List of anomalies | 200 |
| Recommendations | GET | /optimization/recommendations | Service (optional), status (optional) | Paginated recommendations | 200 |
| Update Recommendation | PATCH | /optimization/{id} | Status update | Updated recommendation | 200/404 |
| Delete Cost | DELETE | /cost-data/{id} | ID | Empty | 204/404 |

---

## Extension Requirements

### Security Baseline (ENABLED)
The following security rules are applicable and must be enforced:
- **SECURITY-05**: Input validation on all API parameters
- **SECURITY-08**: Application-level access control (all endpoints are public, no authentication required in this demo)
- **SECURITY-09**: No default credentials or hardcoded secrets
- **SECURITY-15**: Proper error handling with no internal details exposed
- **Additional**: Financial data requires stricter error messaging and logging controls

### Property-Based Testing (ENABLED - Full Enforcement)
The following PBT rules are applicable and must be enforced:
- **PBT-02**: Round-trip properties for serialization/deserialization of cost amounts
- **PBT-03**: Invariant properties for list operations, pagination, and anomaly detection
- **PBT-07**: Domain-specific generators for cost entries, services, and tags
- **PBT-09**: Framework selection and configuration (Python: Hypothesis)
- **PBT-10**: Complementary testing strategy (both example-based and property-based tests)
- **Additional**: Cost calculations must be verified across randomized inputs

---

## Success Criteria

1. ✅ All six core operations implemented and working
2. ✅ Cost data ingestion functional with validation
3. ✅ Daily spending trends with cursor-based pagination and service filtering
4. ✅ Anomaly detection based on 7-day rolling average (>25% spike detection)
5. ✅ Optimization recommendations with status tracking
6. ✅ Proper HTTP status codes and error messages
7. ✅ SQLite database with SQLModel ORM
8. ✅ Comprehensive test coverage including property-based tests for cost calculations
9. ✅ Security and input validation compliance for financial data
10. ✅ Code can run as standalone Python process

---

## Technical Decisions

### Cursor-Based Pagination
Chosen over limit/offset pagination for:
- Consistency: Data remains stable even if new costs are added during pagination
- Performance: Cursor queries typically use indexed lookups
- API stability: Doesn't expose internal record counts

### Anomaly Detection Threshold
25% above 7-day rolling average chosen as initial threshold for:
- Practical detection: Avoids noise while catching genuine spikes
- FinOps relevance: Significant enough to warrant investigation
- Tunable: Can be adjusted based on organizational risk tolerance

### Status Tracking Over Soft Deletes
Recommendations are never deleted, only marked "implemented" or "dismissed" for:
- Audit trail: Full history of all recommendations remains queryable
- Financial accuracy: Can analyze which recommendations were acted upon
- Compliance: Supports FinOps governance and change tracking

### Decimal Precision for Costs
Python `Decimal` type enforced (not float) for:
- Accuracy: No floating-point rounding errors in financial calculations
- Compliance: Industry standard for monetary data
- Testing: Property-based tests can verify exact precision across operations
