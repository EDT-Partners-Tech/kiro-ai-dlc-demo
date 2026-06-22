"""
CloudSpend Analytics API - Main Application

FastAPI application for FinOps cloud cost tracking and optimization.
"""

import os
import logging
import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from contextlib import asynccontextmanager
from typing import Optional
from contextvars import ContextVar

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, text, Numeric
from sqlmodel import Session, select

from app.database import init_db, get_session, engine
from app.models import (
    CostEntry, Tag, Recommendation, RecommendationStatusAudit,
    CostEntryRequest, RecommendationStatusUpdate,
    CostEntryResponse, DailyTrendResponse, DailyTrendsListResponse,
    AnomalyResponse, AnomaliesListResponse, RecommendationResponse,
    RecommendationsListResponse, HealthResponse, ApiInfoResponse
)

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

request_id_context: ContextVar[str] = ContextVar('request_id', default='')


# ============================================================================
# App Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("🛑 Application shutting down")


app = FastAPI(
    title="CloudSpend Analytics API",
    description="FinOps cloud cost tracking and optimization",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)


# ============================================================================
# Middleware & Error Handling
# ============================================================================

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers and request tracing."""
    req_id = str(uuid.uuid4())
    request_id_context.set(req_id)
    
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Request-ID"] = req_id
    return response


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors with a redacted JSON response."""
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    """Handle all unhandled exceptions without leaking internals."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# ============================================================================
# Health Checks
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe: API is running."""
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
async def ready_check(db: Session = Depends(get_session)):
    """Readiness probe: API can serve requests (DB connectivity check)."""
    try:
        db.exec(text("SELECT 1"))
        return HealthResponse(status="ready")
    except Exception as e:
        logger.error(f"DB readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", response_model=ApiInfoResponse)
async def root():
    """API information."""
    return ApiInfoResponse(
        name="CloudSpend Analytics API",
        version="0.1.0",
        docs_url="/docs"
    )


# ============================================================================
# Cost Data Endpoints
# ============================================================================

@app.post("/cost-data", response_model=CostEntryResponse, status_code=201)
async def create_cost(cost_data: CostEntryRequest, db: Session = Depends(get_session)):
    """Ingest cloud cost data."""
    from uuid import uuid4
    
    # Create cost entry
    entry = CostEntry(
        id=str(uuid4()),
        service=cost_data.service,
        amount=cost_data.amount,
        timestamp=cost_data.timestamp,
        created_at=datetime.now(timezone.utc).isoformat() + "Z",
        updated_at=datetime.now(timezone.utc).isoformat() + "Z"
    )
    
    # Create/reference tags (dedup first)
    unique_tags = set(cost_data.tags or [])
    for tag_name in unique_tags:
        tag = db.exec(select(Tag).where(Tag.name == tag_name)).first()
        if not tag:
            tag = Tag(
                id=str(uuid4()),
                name=tag_name,
                created_at=datetime.now(timezone.utc).isoformat() + "Z"
            )
            db.add(tag)
        # Only append if not already in the relationship
        if tag not in entry.tags:
            entry.tags.append(tag)
    
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    return CostEntryResponse(
        id=entry.id,
        service=entry.service,
        amount=entry.amount,
        timestamp=entry.timestamp,
        tags=[tag.name for tag in entry.tags],
        created_at=entry.created_at,
        updated_at=entry.updated_at
    )


@app.get("/cost-data/daily", response_model=DailyTrendsListResponse)
async def get_daily_trends(
    service: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session)
):
    """Get daily spending trends with pagination."""
    import base64
    
    # Parse cursor
    start_date = cursor
    if cursor:
        try:
            start_date = base64.b64decode(cursor).decode()
        except:
            start_date = None
    
    # Build query
    query = select(
        func.date(CostEntry.timestamp).label('date'),
        func.sum(func.cast(CostEntry.amount, Numeric)).label('total')
    )
    
    if service:
        query = query.where(CostEntry.service == service)
    
    query = query.group_by(func.date(CostEntry.timestamp))
    query = query.order_by(func.date(CostEntry.timestamp).desc())
    
    if start_date:
        query = query.where(func.date(CostEntry.timestamp) < start_date)
    
    results = db.exec(query.limit(limit + 1)).all()
    
    has_more = len(results) > limit
    results = results[:limit]
    
    items = [
        DailyTrendResponse(
            date=str(row[0]),
            total_cost=str(row[1]) if row[1] else "0.00",
            cost_count=db.exec(
                select(func.count(CostEntry.id))
                .where(func.date(CostEntry.timestamp) == row[0])
                .where(CostEntry.service == service if service else True)
            ).first() or 0
        )
        for row in results
    ]
    
    next_cursor = None
    if has_more and items:
        next_cursor = base64.b64encode(items[-1].date.encode()).decode()
    
    return DailyTrendsListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        items_count=len(items)
    )


@app.get("/cost-data/anomalies", response_model=AnomaliesListResponse)
async def get_anomalies(
    service: Optional[str] = Query(None),
    db: Session = Depends(get_session)
):
    """Detect spending anomalies (7-day rolling average, 25% threshold)."""
    from datetime import date
    
    anomalies = []
    
    # Get all distinct dates with costs
    dates = db.exec(
        select(func.date(CostEntry.timestamp).label('date'))
        .where(CostEntry.service == service if service else True)
        .group_by(func.date(CostEntry.timestamp))
        .order_by(func.date(CostEntry.timestamp).desc())
    ).all()
    
    for current_date_value in dates:
        if not current_date_value:
            continue

        # SQLite's date() returns text; normalize to a date object for the
        # 7-day arithmetic, and keep ISO strings for the (text-based) comparisons.
        current_date = date.fromisoformat(str(current_date_value))
        current_date_iso = current_date.isoformat()
        baseline_start_iso = (current_date - timedelta(days=7)).isoformat()
        baseline_costs = db.exec(
            select(func.sum(func.cast(CostEntry.amount, Numeric)))
            .where(func.date(CostEntry.timestamp) > baseline_start_iso)
            .where(func.date(CostEntry.timestamp) < current_date_iso)
            .where(CostEntry.service == service if service else True)
        ).first() or Decimal("0")
        
        baseline_dates = db.exec(
            select(func.count(func.distinct(func.date(CostEntry.timestamp))))
            .where(func.date(CostEntry.timestamp) > baseline_start_iso)
            .where(func.date(CostEntry.timestamp) < current_date_iso)
            .where(CostEntry.service == service if service else True)
        ).first() or 0
        
        if baseline_dates == 0:
            baseline_avg = Decimal("0")
        else:
            baseline_avg = Decimal(str(baseline_costs)) / Decimal(baseline_dates)
        
        # Get current day spike
        spike_cost = db.exec(
            select(func.sum(func.cast(CostEntry.amount, Numeric)))
            .where(func.date(CostEntry.timestamp) == current_date_iso)
            .where(CostEntry.service == service if service else True)
        ).first() or Decimal("0")

        spike_cost = Decimal(str(spike_cost))
        
        # Check threshold (25% above baseline)
        if baseline_avg > 0:
            spike_pct = ((spike_cost - baseline_avg) / baseline_avg * 100)
            if spike_pct >= Decimal("25"):
                anomalies.append(AnomalyResponse(
                    date=current_date_iso,
                    service=service or "all",
                    baseline_average=str(baseline_avg),
                    spike_cost=str(spike_cost),
                    spike_percentage=spike_pct
                ))
    
    # Sort by spike percentage descending
    anomalies.sort(key=lambda x: x.spike_percentage, reverse=True)
    
    return AnomaliesListResponse(
        anomalies=anomalies,
        total_count=len(anomalies)
    )


@app.delete("/cost-data/{cost_id}", status_code=204)
async def delete_cost(cost_id: str, db: Session = Depends(get_session)):
    """Delete a cost entry."""
    cost = db.exec(select(CostEntry).where(CostEntry.id == cost_id)).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost entry not found")
    
    db.delete(cost)
    db.commit()
    return None


# ============================================================================
# Optimization Endpoints
# ============================================================================

@app.get("/optimization/recommendations", response_model=RecommendationsListResponse)
async def list_recommendations(
    service: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session)
):
    """List optimization recommendations."""
    import base64
    
    query = select(Recommendation)
    
    if service:
        query = query.where(Recommendation.service == service)
    if status:
        if status not in ("recommended", "implemented", "dismissed"):
            raise HTTPException(status_code=400, detail="Invalid status")
        query = query.where(Recommendation.status == status)
    
    # Savings are stored as TEXT (for Decimal precision), so cast to Numeric
    # to sort by value rather than lexicographically ("30" before "200").
    query = query.order_by(func.cast(Recommendation.estimated_monthly_savings, Numeric).desc())
    
    start_id = cursor
    if cursor:
        try:
            start_id = base64.b64decode(cursor).decode()
        except:
            start_id = None
    
    if start_id:
        start_rec = db.exec(select(Recommendation).where(Recommendation.id == start_id)).first()
        if start_rec:
            query = query.where(
                func.cast(Recommendation.estimated_monthly_savings, Numeric)
                <= Decimal(start_rec.estimated_monthly_savings)
            )
    
    results = db.exec(query.limit(limit + 1)).all()
    
    has_more = len(results) > limit
    results = results[:limit]
    
    items = [
        RecommendationResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            estimated_monthly_savings=r.estimated_monthly_savings,
            service=r.service,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in results
    ]
    
    next_cursor = None
    if has_more and items:
        next_cursor = base64.b64encode(items[-1].id.encode()).decode()
    
    return RecommendationsListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        items_count=len(items)
    )


@app.patch("/optimization/{rec_id}", response_model=RecommendationResponse)
async def update_recommendation(
    rec_id: str,
    update_data: RecommendationStatusUpdate,
    db: Session = Depends(get_session)
):
    """Update recommendation status (one-way transitions: recommended → implemented/dismissed)."""
    from uuid import uuid4
    
    rec = db.exec(select(Recommendation).where(Recommendation.id == rec_id)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    # One-way transition: must be from "recommended"
    if rec.status != "recommended" and update_data.status != rec.status:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {rec.status} to {update_data.status}"
        )
    
    # Create audit log
    audit = RecommendationStatusAudit(
        id=str(uuid4()),
        recommendation_id=rec_id,
        old_status=rec.status,
        new_status=update_data.status,
        timestamp=datetime.now(timezone.utc).isoformat() + "Z"
    )
    
    rec.status = update_data.status
    rec.updated_at = datetime.now(timezone.utc).isoformat() + "Z"
    
    db.add(audit)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    
    return RecommendationResponse(
        id=rec.id,
        title=rec.title,
        description=rec.description,
        estimated_monthly_savings=rec.estimated_monthly_savings,
        service=rec.service,
        status=rec.status,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("ENVIRONMENT") == "development"
    )
