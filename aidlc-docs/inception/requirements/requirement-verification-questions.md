# Requirements Verification Questions

Please answer the following questions to clarify requirements for the blog-posts-api project.

## Question 1
For the list endpoint, what filtering and sorting capabilities are needed beyond tag filtering?

A) Only tag filtering (as mentioned in the initial request)
B) Tag filtering, plus author filtering
C) Tag filtering, author filtering, and date range filtering
D) Comprehensive filtering (tags, author, date range, status) and sorting options
E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
Should the list endpoint support multiple tags (e.g., posts tagged with BOTH tag1 AND tag2, or posts with EITHER tag1 OR tag2)?

A) Single tag filtering only
B) Multiple tags with AND logic (post must have all specified tags)
C) Multiple tags with OR logic (post must have at least one specified tag)
D) Both AND and OR support (user specifies which logic to use)
E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
What validation and constraints are needed for blog post fields?

A) Basic validation only (title and content are required, non-empty)
B) Basic validation plus field length limits (e.g., title max 200 chars)
C) Comprehensive validation including character limits, HTML escaping, and allowed characters
D) Enhanced validation with custom business rules (e.g., duplicate title checking)
E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
How should pagination work for the list endpoint?

A) Limit/offset pagination only
B) Cursor-based pagination only
C) Both limit/offset AND cursor-based options
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 5
What should the default and maximum page sizes be for the list endpoint?

A) Default 10, Max 50
B) Default 20, Max 100
C) Default 50, Max 200
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 6
Should the API support batch operations (e.g., delete multiple posts, add tags to multiple posts)?

A) No batch operations (only single-item operations)
B) Yes, implement batch delete
C) Yes, implement batch operations for delete, update, and tag management
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
What error handling and HTTP status codes are expected?

A) Basic error handling (400 Bad Request, 404 Not Found, 500 Internal Server Error)
B) Standard REST error handling with detailed error messages and proper status codes
C) Enhanced error handling with error codes, validation details, and request ID tracking
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 8
Should the API include metadata in responses (e.g., pagination info, response timestamps)?

A) No metadata, just the data
B) Minimal metadata (pagination info for list responses)
C) Standard metadata (pagination, timestamps, response status indicators)
D) Extended metadata (pagination, timestamps, API version, response times)
E) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 9: Security Baseline Extension
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10: Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)
B) Partial — enforce PBT rules only for pure functions and serialization round-trips (suitable for projects with limited algorithmic complexity)
C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)
D) Other (please describe after [Answer]: tag below)

[Answer]: A

