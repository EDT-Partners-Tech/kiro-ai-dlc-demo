# NFR Design Plan - API Service

## Unit: blog-posts-api (FastAPI REST Service)

### Design Focus Areas

- [ ] Security Patterns - Input validation, error handling, logging design
- [ ] Resilience Patterns - Error recovery and failure handling
- [ ] Performance Patterns - Pagination and query optimization
- [ ] Testing Architecture - Property-based and example-based test structure
- [ ] Logical Components - Request handlers, data models, database layer

---

## NFR Design Clarification Questions

### Question 1: Error Recovery Strategy
How should the API handle database connection failures?

A) Fail fast - Return 500 error immediately if database unavailable
B) Retry once - Attempt one automatic retry before returning error
C) Retry with backoff - Exponential backoff with max 3 retries
D) Circuit breaker - Track failures, trip circuit after threshold, fail fast temporarily
E) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2: Input Validation Approach
Where should input validation occur?

A) Request model only - Pydantic validation at API layer
B) Request + business logic - Pydantic + domain-level validation
C) Multi-layer - Request + business + database constraints
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3: SQL Query Safety
How should SQL injection prevention be implemented?

A) ORM-only - Use SQLModel ORM exclusively, no raw SQL
B) ORM + prepared statements - ORM for main queries, prepared statements for complex queries
C) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4: Pagination Cursor Implementation
How should cursor values be encoded?

A) Plain - Use post ID directly as cursor (e.g., "5")
B) Base64 - Encode post ID in Base64 for obfuscation (e.g., "NQ==")
C) Signed token - Use JWT or HMAC-signed cursor for tamper-proofing
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 5: Error Response Format
What information should error responses include?

A) Basic - Status code and brief message only
B) Standard - Status code, message, and error type/code
C) Detailed - Status code, message, error code, field-level details for validation
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 6: Logging Strategy for API Requests
What should be logged for each API request?

A) Minimal - Status code and path only
B) Standard - Method, path, status code, response time, client IP
C) Detailed - Plus request/response body and query parameters
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 7: Tag Filtering Performance
For filtering by tags, which approach is preferred?

A) Eager loading - Load all posts with all tags, filter in Python
B) SQL query - Use SQL JOIN to filter at database level
C) Indexed - Tag index for efficient filtering
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 8: Concurrent Request Handling
How should concurrent requests to the same resource be handled?

A) Last-write-wins - Later updates overwrite earlier ones
B) Optimistic locking - Track version numbers, reject if stale
C) Pessimistic locking - Lock resource during update
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 9: Test Organization
How should tests be organized?

A) Single file - All tests in one test file
B) By layer - Separate test files for API, business logic, database layers
C) By feature - Separate test files for each feature (posts, tags, pagination)
D) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 10: Property-Based Testing Scope
Which components should have property-based tests?

A) Models only - PBT for data models and serialization
B) Models + endpoints - PBT for models and API endpoint contracts
C) Full coverage - PBT for models, endpoints, and business logic
D) Other (please describe after [Answer]: tag below)

[Answer]: A 

---

## Next Steps

Once you've answered all 10 questions, I will:

1. Analyze your responses for clarity and consistency
2. Generate the NFR Design Patterns document
3. Generate the Logical Components document
4. Present both for your review and approval

Please fill in all [Answer]: tags with your selections (A, B, C, D, or E) and let me know when done.
