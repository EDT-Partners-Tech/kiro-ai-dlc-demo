# Deployment Configuration - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: Infrastructure Design  
**Date**: 2026-06-19

---

## Overview

This document specifies deployment configuration, environment variables, and operational setup for the Cost Analytics Service.

---

## Environment Variables

### Core Configuration

| Variable | Value (Demo) | Value (Production) | Purpose |
|----------|-------------|-------------------|---------|
| `DATABASE_URL` | `sqlite:///./cloudspend.db` | `postgresql://user:pass@rds-host/db` | Database connection string |
| `ENVIRONMENT` | `development` | `production` | Affects logging verbosity, debug mode |
| `LOG_LEVEL` | `INFO` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `API_HOST` | `127.0.0.1` | `0.0.0.0` | API listen address |
| `API_PORT` | `8000` | `8000` | API listen port |

### Optional Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_POOL_SIZE` | `5` | Min connection pool size |
| `DATABASE_POOL_MAX_OVERFLOW` | `15` | Max overflow connections (total = 20) |
| `DATABASE_POOL_TIMEOUT` | `30` | Timeout for acquiring connection (seconds) |
| `REQUEST_TIMEOUT_SECONDS` | `30` | Request timeout (for long queries like anomalies) |
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins (restrict in production) |

---

## Startup Configuration

### Demo Startup (Local Development)

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Export environment variables (optional, defaults work)
export DATABASE_URL="sqlite:///./cloudspend.db"
export LOG_LEVEL="DEBUG"
export ENVIRONMENT="development"

# 5. Start server (with auto-reload)
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 6. Access API
# Swagger UI: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc
# Health check: http://127.0.0.1:8000/health
```

### Production Startup (Single EC2 Instance)

```bash
#!/bin/bash
# deployment.sh

set -e

# Set environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export DATABASE_URL=postgresql://user:pass@rds-prod.aws.amazon.com:5432/cloudspend
export API_HOST=0.0.0.0
export API_PORT=8000

# Install dependencies
pip install -r requirements.txt

# Run migrations (if needed)
# alembic upgrade head  # Future: database migrations

# Start server (gunicorn for production)
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

---

## Container Deployment (Optional Docker)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY app/ ./app/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Environment
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO
ENV DATABASE_URL=postgresql://user:pass@rds-host/cloudspend
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

```bash
# Build image
docker build -t cloudspend-api:latest .

# Run locally (map port 8000)
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///./cloudspend.db" \
  -e LOG_LEVEL="INFO" \
  cloudspend-api:latest

# Run on ECS (via docker run with RDS connection)
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e ENVIRONMENT="production" \
  cloudspend-api:latest
```

---

## Database Initialization

### Local SQLite Setup

```python
# app/database.py
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cloudspend.db")

engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", 5)),
    max_overflow=int(os.getenv("DATABASE_POOL_MAX_OVERFLOW", 15)),
    pool_pre_ping=True,
)

def init_db():
    """Create all tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency: get DB session"""
    with Session(engine) as session:
        yield session
```

### Initialize on Startup

```python
# main.py
from contextlib import asynccontextmanager
from app.database import init_db

@asynccontextmanager
async def lifespan(app):
    # Startup
    init_db()
    print("✅ Database initialized")
    yield
    # Shutdown (if needed)
    print("🛑 Shutting down")

app = FastAPI(lifespan=lifespan)
```

### Production RDS Setup

For RDS PostgreSQL:
1. Create RDS instance via AWS Console or IaC (Terraform, CloudFormation)
2. Set `DATABASE_URL` environment variable to RDS endpoint
3. Run migrations (via Alembic, if implemented)
4. SQLAlchemy creates tables automatically (or via migration tool)

---

## Logging Configuration

### Structured JSON Logging

```python
# app/logging.py
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    
    # JSON formatter
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(request_id)s %(level)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    
    # Set level
    level = os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, level))
    
    return logger
```

### Log Output Example

```json
{
  "timestamp": "2026-06-19T10:30:45Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "level": "INFO",
  "message": "POST /cost-data 201 45ms",
  "method": "POST",
  "path": "/cost-data",
  "status": 201,
  "latency_ms": 45
}
```

### Production Logging (CloudWatch Integration)

CloudWatch agent can tail stdout and ingest JSON logs:

```bash
# Install CloudWatch agent
# Configure /opt/aws/amazon-cloudwatch-agent/etc/config.json
# Point to stdout of container/process
# JSON logs automatically parsed and indexed
```

---

## Health Check Configuration

### Kubernetes Readiness Probe

```yaml
# kubernetes-deployment.yaml (example)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudspend-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: cloudspend-api:latest
        ports:
        - containerPort: 8000
        
        # Liveness probe (is process alive?)
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        
        # Readiness probe (can handle traffic?)
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

## Performance Tuning

### Database Connection Pool

**Demo**: min=5, max=20 (default)

**Production Tuning**:
- Calculate based on: (avg_response_time * req_per_sec) + buffer
- Example: 100ms avg, 10 req/sec, buffer=2 → pool_size = (0.1 * 10) + 2 = 3 (start small)
- Monitor and adjust based on `pool exhausted` errors

### Query Timeouts

**Demo**: 30 seconds (generous)

**Production**:
- Normal queries: 5 seconds
- Anomaly detection: 30 seconds (complex aggregation)
- Adjust if anomaly queries timeout frequently

### Uvicorn Workers

**Demo**: 1 worker (auto-reload mode)

**Production** (via gunicorn):
- Workers = (2 * CPU_cores) + 1
- Example: 4 CPU cores → 9 workers
- Gunicorn load-balances requests to workers

---

## Backup & Recovery

### Local SQLite Backups

```bash
# Manual backup
cp cloudspend.db cloudspend.db.backup.$(date +%Y%m%d-%H%M%S)

# Schedule daily backup (cron)
0 2 * * * cp /path/to/cloudspend.db /backups/cloudspend.db.$(date +\%Y\%m\%d)
```

### RDS Backups (Production)

AWS RDS automatic backups (enabled by default):
- Retention: 7 days (configurable)
- Automated snapshots: Daily
- Manual snapshots: On-demand

Recovery process:
1. Create RDS restore from snapshot
2. Update `DATABASE_URL` to point to new instance
3. Restart API service

---

## Monitoring & Observability

### CloudWatch Metrics (Production)

```python
# Send custom metrics to CloudWatch
import boto3

cloudwatch = boto3.client('cloudwatch')

def emit_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='CloudSpendAPI',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
        }]
    )

# In API:
# emit_metric('RequestCount', 1)
# emit_metric('ResponseLatency', latency_ms, unit='Milliseconds')
```

### CloudWatch Alarms (Production)

```python
# Alert if error rate > 5%
# Alert if latency p99 > 1000ms
# Alert if database connection pool exhausted
```

---

## Disaster Recovery Plan

### RTO/RPO Targets

| Metric | Demo | Production |
|--------|------|-----------|
| RTO (Recovery Time Objective) | 5 minutes (manual restore) | <30 minutes (RDS snapshot restore) |
| RPO (Recovery Point Objective) | 1 day (manual backups) | 1 hour (RDS automated backups) |

### Recovery Procedure

1. **Detect Issue**: Health check fails or error rate spikes
2. **Diagnosis**: Check CloudWatch logs for root cause
3. **Restore**: 
   - Demo: `cp cloudspend.db.backup cloudspend.db`
   - Production: RDS snapshot restore
4. **Verify**: Run health checks
5. **Monitor**: Watch metrics for stability

---

## Scaling Strategy

### Phase 1: Demo (Current)
- Single SQLite instance
- Local or small EC2 instance
- Manual backups

### Phase 2: Single-Instance Production
- Single RDS PostgreSQL instance (db.t3.medium)
- Single EC2 instance (t3.medium)
- Automated RDS backups

### Phase 3: High-Availability Production
- RDS Multi-AZ (automatic failover)
- Multiple EC2 instances + load balancer
- CloudWatch monitoring + alarms

### Phase 4: Global Scale
- RDS read replicas (multi-region)
- ECS/Fargate for API (auto-scaling)
- CloudFront CDN for static content

---

## Summary

**Deployment Configuration Principles**:
- ✅ Environment variables for all config (no hardcoding)
- ✅ Local development works out-of-box (SQLite)
- ✅ Production-ready (RDS support, structured logging, health checks)
- ✅ Clear scaling path (local → EC2 → ECS → Global)
- ✅ Observability from day one (JSON logs, health checks, metrics)

**Ready for Code Generation**: Infrastructure is well-defined and reproducible.
