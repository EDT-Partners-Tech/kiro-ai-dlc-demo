"""Seed data for CloudSpend Analytics API."""

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import CostEntry, Tag, Recommendation

def seed_data():
    """Populate database with sample FinOps data for demo and testing."""

    # Ensure tables exist before seeding (safe/idempotent if app already created them).
    # Models are imported above, so SQLModel.metadata is populated by this point.
    init_db()

    with Session(engine) as session:
        # Check if data already seeded
        existing_entries = session.exec(select(CostEntry)).first()
        if existing_entries:
            return
        
        now = datetime.now(timezone.utc)
        created_at = now.isoformat() + "Z"
        
        # Create sample tags
        tags_data = [
            ("production", "Production environment"),
            ("staging", "Staging environment"),
            ("development", "Development environment"),
            ("web", "Web tier"),
            ("database", "Database tier"),
            ("storage", "Storage tier"),
        ]
        
        tags = {}
        for tag_name, _ in tags_data:
            tag = Tag(
                id=f"tag-{tag_name}",
                name=tag_name,
                created_at=created_at
            )
            session.add(tag)
            tags[tag_name] = tag
        
        session.flush()
        
        # Create sample cost entries (last 30 days)
        services_config = {
            "EC2": {
                "tags": ["production", "web"],
                "base_cost": Decimal("500"),
                "variance": Decimal("100"),
            },
            "RDS": {
                "tags": ["production", "database"],
                "base_cost": Decimal("300"),
                "variance": Decimal("50"),
            },
            "S3": {
                "tags": ["production", "storage"],
                "base_cost": Decimal("100"),
                "variance": Decimal("30"),
            },
            "Lambda": {
                "tags": ["production", "web"],
                "base_cost": Decimal("50"),
                "variance": Decimal("20"),
            },
        }
        
        for day_offset in range(30):
            date = now - timedelta(days=day_offset)
            
            for service, config in services_config.items():
                # Add some daily variation (pattern: higher on weekdays)
                weekday = date.weekday()
                variation = Decimal("1.2") if weekday < 5 else Decimal("0.8")
                daily_cost = config["base_cost"] * variation
                
                entry = CostEntry(
                    id=f"cost-{service}-{day_offset}",
                    service=service,
                    amount=str(daily_cost),
                    timestamp=date.isoformat(),
                    created_at=created_at,
                    updated_at=created_at
                )
                
                # Assign tags
                for tag_name in config["tags"]:
                    if tag_name in tags:
                        entry.tags.append(tags[tag_name])
                
                session.add(entry)
        
        # Create sample recommendations
        recommendations_data = [
            {
                "id": "rec-1",
                "title": "Right-size EC2 instances",
                "description": "Your t2.large instances are consistently underutilized (avg 20% CPU). Consider t2.medium.",
                "service": "EC2",
                "status": "recommended",
                "savings": Decimal("150"),
            },
            {
                "id": "rec-2",
                "title": "Use RDS Reserved Instances",
                "description": "Convert on-demand RDS to 3-year Reserved Instances for 70% discount.",
                "service": "RDS",
                "status": "recommended",
                "savings": Decimal("200"),
            },
            {
                "id": "rec-3",
                "title": "Enable S3 Lifecycle Policies",
                "description": "Move old objects to Glacier automatically after 30 days.",
                "service": "S3",
                "status": "recommended",
                "savings": Decimal("30"),
            },
            {
                "id": "rec-4",
                "title": "Consolidate Lambda layers",
                "description": "Current Lambda structure has duplicate dependencies across layers.",
                "service": "Lambda",
                "status": "implemented",
                "savings": Decimal("25"),
            },
        ]
        
        for rec_data in recommendations_data:
            rec = Recommendation(
                id=rec_data["id"],
                title=rec_data["title"],
                description=rec_data["description"],
                service=rec_data["service"],
                status=rec_data["status"],
                estimated_monthly_savings=str(rec_data["savings"]),
                created_at=created_at,
                updated_at=created_at
            )
            session.add(rec)
        
        session.commit()
        print("✅ Sample data seeded successfully")


if __name__ == "__main__":
    seed_data()
