from datetime import date, datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.carbon_calculator import calculate_emissions_kg, normalize_category_name, seed_default_emission_factors
from app.config import CORS_ORIGINS
from app.database import Base, SessionLocal, engine, get_db
from app.migrations import migrate_co2e_only, migrate_factor_metadata, migrate_legacy_account_schema
from app.models import Activity, Category, EmissionFactor, EmissionRecord, Goal
from app.schemas import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    CategoryRead,
    EmissionFactorRead,
    GoalCreate,
    GoalRead,
    GoalUpdate,
)

migrate_factor_metadata(engine)
migrate_co2e_only(engine)
migrate_legacy_account_schema(engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EcoMeter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed_default_categories(db: Session) -> None:
    default_categories = [
        ("Transportation", "Passenger travel and direct active-transport emissions"),
        ("Electricity", "2026 Indian grid electricity estimate"),
        ("Food", "Daily dietary estimates by pattern"),
        ("Shopping", "Product-specific and illustrative consumer-goods estimates"),
        ("Waste", "Organic, inorganic, and electronic waste treatment estimates"),
    ]
    for name, description in default_categories:
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            db.add(Category(name=name, description=description))
        elif category.description != description:
            category.description = description
    db.commit()


with SessionLocal() as db:
    seed_default_categories(db)
    seed_default_emission_factors(db)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "EcoMeter API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.query(Category).order_by(Category.name.asc()).all()


@app.get("/emission-factors", response_model=list[EmissionFactorRead])
def list_emission_factors(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(EmissionFactor)
    query = query.filter(EmissionFactor.gas_basis == "CO2e")
    category_name = normalize_category_name(category) if category else None
    if category_name:
        query = query.filter(EmissionFactor.category == category_name)
    factors = [
        {
            "category": factor.category,
            "activity_type": factor.activity_type,
            "emission_factor": factor.emission_factor,
            "unit": factor.unit,
            "source": factor.source,
            "reference_year": factor.reference_year,
            "source_url": factor.source_url,
            "geography": factor.geography,
            "gas_basis": factor.gas_basis,
            "methodology": factor.methodology,
            "verification_status": factor.verification_status,
            "notes": factor.notes,
            "available": True,
        }
        for factor in query.all()
    ]
    return sorted(factors, key=lambda factor: (factor["category"], factor["activity_type"]))


@app.post("/activities", response_model=ActivityRead)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)) -> Activity:
    category_name = normalize_category_name(payload.category)
    category = db.query(Category).filter(Category.name == category_name).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown category: {category_name}")

    factor = db.query(EmissionFactor).filter(
        EmissionFactor.category == category_name,
        EmissionFactor.activity_type == payload.activity_type,
    ).first()
    if not factor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No emission factor for {payload.activity_type}")
    if factor.gas_basis != "CO2e":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="EcoMeter only supports emission factors reported in CO2e.",
        )

    quantity = float(payload.quantity)
    if payload.unit != factor.unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit for {payload.activity_type} must be {factor.unit}",
        )

    calculated = calculate_emissions_kg(db, category_name, payload.activity_type, quantity)
    activity = Activity(
        category_id=category.id,
        activity_type=payload.activity_type,
        quantity=quantity,
        unit=factor.unit,
        activity_date=payload.activity_date,
        notes=payload.notes,
        calculated_emissions_kg=calculated,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    record = EmissionRecord(
        activity_id=activity.id,
        category=category_name,
        activity_type=payload.activity_type,
        quantity=quantity,
        unit=factor.unit,
        co2e_kg=calculated,
        recorded_date=payload.activity_date,
    )
    db.add(record)
    db.commit()
    db.refresh(activity)
    return {
        "id": activity.id,
        "category": category_name,
        "activity_type": activity.activity_type,
        "quantity": activity.quantity,
        "unit": activity.unit,
        "activity_date": activity.activity_date,
        "notes": activity.notes,
        "calculated_emissions_kg": activity.calculated_emissions_kg,
        "created_at": activity.created_at,
    }


@app.get("/activities", response_model=list[ActivityRead])
def list_activities(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    activities = (
        db.query(Activity)
        .order_by(Activity.activity_date.desc(), Activity.id.desc())
        .all()
    )
    return [
        {
            "id": activity.id,
            "category": activity.category.name,
            "activity_type": activity.activity_type,
            "quantity": activity.quantity,
            "unit": activity.unit,
            "activity_date": activity.activity_date,
            "notes": activity.notes,
            "calculated_emissions_kg": activity.calculated_emissions_kg,
            "created_at": activity.created_at,
        }
        for activity in activities
    ]


@app.get("/activities/{activity_id}", response_model=ActivityRead)
def get_activity(activity_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return {
        "id": activity.id,
        "category": activity.category.name,
        "activity_type": activity.activity_type,
        "quantity": activity.quantity,
        "unit": activity.unit,
        "activity_date": activity.activity_date,
        "notes": activity.notes,
        "calculated_emissions_kg": activity.calculated_emissions_kg,
        "created_at": activity.created_at,
    }


@app.put("/activities/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if payload.category:
        category_name = normalize_category_name(payload.category)
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown category: {category_name}")
        activity.category_id = category.id
    if payload.activity_type:
        activity.activity_type = payload.activity_type
    if payload.quantity is not None:
        activity.quantity = float(payload.quantity)
    if payload.activity_date:
        activity.activity_date = payload.activity_date
    if payload.notes is not None:
        activity.notes = payload.notes

    factor = db.query(EmissionFactor).filter(
        EmissionFactor.category == activity.category.name,
        EmissionFactor.activity_type == activity.activity_type,
    ).first()
    if not factor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No emission factor for {activity.activity_type}")
    if factor.gas_basis != "CO2e":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="EcoMeter only supports emission factors reported in CO2e.",
        )
    if payload.unit is not None and payload.unit != factor.unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit for {activity.activity_type} must be {factor.unit}",
        )
    activity.unit = factor.unit
    activity.calculated_emissions_kg = calculate_emissions_kg(db, activity.category.name, activity.activity_type, activity.quantity)

    record = db.query(EmissionRecord).filter(EmissionRecord.activity_id == activity.id).first()
    if record:
        record.category = activity.category.name
        record.activity_type = activity.activity_type
        record.quantity = activity.quantity
        record.unit = activity.unit
        record.co2e_kg = activity.calculated_emissions_kg
        record.recorded_date = activity.activity_date
    else:
        db.add(
            EmissionRecord(
                activity_id=activity.id,
                category=activity.category.name,
                activity_type=activity.activity_type,
                quantity=activity.quantity,
                unit=activity.unit,
                co2e_kg=activity.calculated_emissions_kg,
                recorded_date=activity.activity_date,
            )
        )

    db.commit()
    db.refresh(activity)
    return {
        "id": activity.id,
        "category": activity.category.name,
        "activity_type": activity.activity_type,
        "quantity": activity.quantity,
        "unit": activity.unit,
        "activity_date": activity.activity_date,
        "notes": activity.notes,
        "calculated_emissions_kg": activity.calculated_emissions_kg,
        "created_at": activity.created_at,
    }


@app.delete("/activities/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    db.query(EmissionRecord).filter(EmissionRecord.activity_id == activity.id).delete()
    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully"}


@app.get("/emissions/summary")
def get_summary(
    db: Session = Depends(get_db),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> dict[str, Any]:
    today = datetime.utcnow().date()
    if start_date is None:
        start_date = today - timedelta(days=30)
    if end_date is None:
        end_date = today

    activities = (
        db.query(Activity)
        .filter(
            Activity.activity_date >= start_date,
            Activity.activity_date <= end_date,
        )
        .all()
    )

    def total_for(predicate) -> float:
        return round(
            sum(
                float(activity.calculated_emissions_kg)
                for activity in activities
                if predicate(activity)
            ),
            3,
        )

    today_total = total_for(lambda activity: activity.activity_date == today)
    week_start = today - timedelta(days=today.weekday())
    week_total = total_for(lambda activity: week_start <= activity.activity_date <= today)
    month_start = date(today.year, today.month, 1)
    month_total = total_for(lambda activity: activity.activity_date >= month_start)

    active_goal = (
        db.query(Goal)
        .filter(Goal.is_active.is_(True))
        .order_by(Goal.created_at.desc())
        .first()
    )
    goal_progress = 0.0
    goal_remaining = 0.0
    if active_goal:
        goal_remaining = max(float(active_goal.monthly_target_kg) - month_total, 0.0)
        goal_progress = round((month_total / active_goal.monthly_target_kg) * 100, 2) if active_goal.monthly_target_kg else 0.0

    breakdown = (
        db.query(
            Category.name.label("category"),
            func.sum(Activity.calculated_emissions_kg).label("total_kg"),
        )
        .join(Activity, Activity.category_id == Category.id)
        .filter(Activity.activity_date >= start_date, Activity.activity_date <= end_date)
        .group_by(Category.name)
        .all()
    )

    recommendations = build_recommendations(activities)
    recent = (
        db.query(Activity)
        .order_by(Activity.activity_date.desc(), Activity.id.desc())
        .limit(5)
        .all()
    )

    recent_payload = [
        {
            "id": activity.id,
            "category": activity.category.name,
            "activity_type": activity.activity_type,
            "quantity": activity.quantity,
            "unit": activity.unit,
            "activity_date": activity.activity_date,
            "notes": activity.notes,
            "calculated_emissions_kg": activity.calculated_emissions_kg,
            "created_at": activity.created_at,
        }
        for activity in recent
    ]

    return {
        "today_kg_co2e": today_total,
        "week_kg_co2e": week_total,
        "month_kg_co2e": month_total,
        "average_daily_kg_co2e": round(month_total / max(today.day, 1), 3),
        "active_goal": {
            "id": active_goal.id,
            "monthly_target_kg": active_goal.monthly_target_kg,
            "start_month": active_goal.start_month,
            "is_active": active_goal.is_active,
            "created_at": active_goal.created_at,
        } if active_goal else None,
        "goal_progress_percent": goal_progress,
        "goal_remaining_kg": goal_remaining,
        "breakdown": [
            {"category": item[0], "total_kg": round(float(item[1]), 3)}
            for item in breakdown
        ],
        "recommendations": recommendations,
        "recent_activities": recent_payload,
    }


@app.get("/emissions/breakdown")
def get_breakdown(
    db: Session = Depends(get_db),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> list[dict[str, Any]]:
    today = datetime.utcnow().date()
    if start_date is None:
        start_date = today - timedelta(days=30)
    if end_date is None:
        end_date = today

    rows = (
        db.query(
            Category.name.label("category"),
            func.sum(Activity.calculated_emissions_kg).label("total_kg"),
        )
        .join(Activity, Activity.category_id == Category.id)
        .filter(Activity.activity_date >= start_date, Activity.activity_date <= end_date)
        .group_by(Category.name)
        .all()
    )
    return [
        {"category": row[0], "total_kg": round(float(row[1]), 3)}
        for row in rows
    ]


@app.get("/emissions/trends")
def get_trends(
    db: Session = Depends(get_db),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    today = datetime.utcnow().date()
    if start_date is None:
        start_date = today - timedelta(days=30)
    if end_date is None:
        end_date = today
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date must be on or before end date")
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a date range of 366 days or fewer")

    query = (
        db.query(
            Activity.activity_date,
            func.sum(Activity.calculated_emissions_kg),
        )
        .filter(Activity.activity_date >= start_date, Activity.activity_date <= end_date)
    )
    if category and category.lower() != "all categories":
        query = query.join(Category, Activity.category_id == Category.id).filter(
            Category.name == normalize_category_name(category)
        )
    totals_by_day: dict[date, float] = {
        row[0]: float(row[1])
        for row in query.group_by(Activity.activity_date).all()
    }

    day_cursor = start_date
    rows: list[dict[str, Any]] = []
    while day_cursor <= end_date:
        rows.append({
            "date": day_cursor.isoformat(),
            "total_kg_co2e": round(totals_by_day.get(day_cursor, 0.0), 3),
        })
        day_cursor += timedelta(days=1)
    return rows


@app.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db)) -> list[dict[str, str]]:
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=30)
    activities = (
        db.query(Activity)
        .filter(Activity.activity_date >= start_date)
        .all()
    )
    return build_recommendations(activities)


def build_recommendations(activities: list[Activity]) -> list[dict[str, str]]:
    category_totals: dict[str, float] = {}
    for activity in activities:
        category_totals[activity.category.name] = category_totals.get(activity.category.name, 0.0) + float(activity.calculated_emissions_kg)

    recommendations: list[dict[str, str]] = []
    if category_totals.get("Transportation", 0) > 15:
        recommendations.append({
            "title": "Reduce transport emissions",
            "description": "Your transport emissions are high. Consider public transport, carpooling, biking, or combining errands into one trip.",
            "priority": "High",
        })
    if category_totals.get("Electricity", 0) > 12:
        recommendations.append({
            "title": "Lower electricity use",
            "description": "Switch off unused devices, use LED lighting, and unplug chargers to reduce unnecessary electricity consumption.",
            "priority": "High",
        })
    if category_totals.get("Food", 0) > 10:
        recommendations.append({
            "title": "Choose lower-carbon meals",
            "description": "Try vegetarian or vegan meals more often to reduce food-related emissions while keeping nutrition balanced.",
            "priority": "Medium",
        })
    if category_totals.get("Waste", 0) > 8:
        recommendations.append({
            "title": "Improve waste separation",
            "description": "Compost organic waste and recycle more to reduce waste-related emissions and landfill impacts.",
            "priority": "Medium",
        })
    if not recommendations:
        recommendations.append({
            "title": "Good progress",
            "description": "Your recent activity pattern is sustainable. Keep monitoring your weekly totals and continue reducing high-impact habits.",
            "priority": "Low",
        })
    return recommendations


@app.post("/goals", response_model=GoalRead)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)) -> Goal:
    existing = db.query(Goal).filter(Goal.is_active.is_(True)).first()
    if existing:
        existing.is_active = False
    goal = Goal(
        monthly_target_kg=payload.monthly_target_kg,
        start_month=payload.start_month,
        is_active=True,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@app.get("/goals", response_model=list[GoalRead])
def list_goals(db: Session = Depends(get_db)) -> list[Goal]:
    return db.query(Goal).order_by(Goal.created_at.desc()).all()


@app.put("/goals/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    if payload.monthly_target_kg is not None:
        goal.monthly_target_kg = payload.monthly_target_kg
    if payload.start_month is not None:
        goal.start_month = payload.start_month
    if payload.is_active is not None:
        goal.is_active = payload.is_active
    db.commit()
    db.refresh(goal)
    return goal


@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted successfully"}
