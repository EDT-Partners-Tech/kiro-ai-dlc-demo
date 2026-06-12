# AWS Services Priority

## Principle
When designing and implementing new features, prioritize AWS services as the primary solution before considering third-party libraries or custom implementations.

## Application Scope
This applies to:
- New feature design in Requirements Analysis phase
- Technology stack decisions in NFR Requirements phase
- Implementation planning in Code Generation phase
- Architecture decisions in NFR Design phase

## AWS Service Selection Process

When evaluating how to implement a new feature, follow this decision tree:

### 1. **Identify the Requirement**
Clearly define what capability or service the feature needs (e.g., authentication, data storage, messaging, image processing, etc.)

### 2. **Research Applicable AWS Services**
- Check AWS documentation for services that address the requirement
- Common categories:
  - **Storage & Databases**: S3, DynamoDB, RDS, Aurora, ElastiCache
  - **Compute**: EC2, Lambda, ECS, Fargate
  - **Networking**: VPC, CloudFront, API Gateway, ALB
  - **Authentication & Authorization**: Cognito, IAM
  - **Messaging & Queuing**: SQS, SNS, EventBridge
  - **Machine Learning**: SageMaker, Bedrock, Rekognition, Textract
  - **Monitoring & Logging**: CloudWatch, X-Ray
  - **Security**: Secrets Manager, KMS, WAF
  - **Serverless Integration**: Lambda, Step Functions, EventBridge

### 3. **Evaluate AWS Services First**
- Assess fit, cost, scalability, and management overhead
- Document why an AWS service is suitable or unsuitable
- Note trade-offs (managed service vs. custom control)

### 4. **Consider Alternatives Only If**
AWS services don't meet the requirement due to:
- Unsupported feature or capability gap
- Cost prohibitive for the use case
- Architectural mismatch with existing design
- Explicit project constraint (e.g., multi-cloud requirement)

When documenting alternatives, explicitly state why the AWS service was rejected.

### 5. **Document the Decision**
In NFR Requirements or Tech Stack Decisions, include:
- Selected AWS service(s) with justification
- Alternative considered (if any) with rejection rationale
- Integration approach with existing architecture

## Examples

### ✅ Good: Prioritizing AWS
**Feature**: Add image thumbnail generation on post upload

**Decision**: 
- Selected: **AWS Lambda + S3 + EventBridge**
- Rationale: Serverless, auto-scales, integrates with S3 events, pay-per-use
- Alternative: Custom image processing service → Rejected (requires infrastructure management, higher operational overhead)

### ✅ Good: Clear Rejection Rationale
**Feature**: Add real-time user presence tracking

**Decision**:
- Selected: **Amazon Kinesis + DynamoDB**
- Rationale: Real-time streaming, managed service, built for low-latency state tracking
- Alternative: Custom Redis cluster → Rejected (requires operational management, AWS Elasticache could also work but Kinesis better for streaming use case)

### ❌ Poor: Skipping AWS Evaluation
**Feature**: Add caching layer

**Decision**: Use Redis library directly without evaluating **ElastiCache** (AWS managed Redis service)
- Problem: Missed managed service option that reduces operational burden

## Integration with Existing Architecture

This project:
- **Runtime**: Python + FastAPI (on Lambda via Uvicorn or locally via Uvicorn)
- **Data Layer**: SQLite → Consider migrating to **RDS** or **DynamoDB** as features scale
- **Observability**: Consider **CloudWatch** for logs and **X-Ray** for tracing
- **Security**: Consider **Secrets Manager** for sensitive configuration
- **API Gateway**: Consider **API Gateway** service for API management and rate limiting

## Conflicts with Other Principles

If AWS service prioritization conflicts with other project goals:
1. Document the conflict explicitly
2. Escalate to stakeholders for decision
3. Record the decision and rationale in audit.md

Example: If a feature requires **maximum portability** (multi-cloud), that may override AWS prioritization. State this clearly in requirements.

## When AWS Services Don't Exist

For capabilities genuinely not covered by AWS services (as of today):
1. Use well-maintained, popular open-source libraries
2. Document why AWS was unable to meet the requirement
3. Consider OSS options that integrate well with AWS (e.g., OpenTelemetry for observability)

## Review Checklist

Before implementing a feature, confirm:
- [ ] Feature requirement clearly defined
- [ ] AWS service(s) researched for this requirement
- [ ] AWS service evaluated for fit, cost, scale
- [ ] If not selected: rejection rationale documented
- [ ] If selected: integration approach with architecture defined
- [ ] Decision logged in requirements or tech-stack decisions document
