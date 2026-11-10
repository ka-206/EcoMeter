from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivityCreate(BaseModel):
    category: str
    activity_type: str
    quantity: float = Field(..., gt=0)
    unit: str
    activity_date: date
    notes: str | None = None


class ActivityUpdate(BaseModel):
    category: str | None = None
    activity_type: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    activity_date: date | None = None
    notes: str | None = None


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    activity_type: str
    quantity: float
    unit: str
    activity_date: date
    notes: str | None = None
    calculated_emissions_kg: float
    created_at: datetime


class EmissionFactorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    category: str
    activity_type: str
    emission_factor: float | None
    unit: str
    source: str
    reference_year: int
    source_url: str | None = None
    geography: str | None = None
    gas_basis: str | None = None
    methodology: str | None = None
    verification_status: str | None = None
    notes: str | None = None
    available: bool = True


class GoalCreate(BaseModel):
    monthly_target_kg: float = Field(..., gt=0)
    start_month: str


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monthly_target_kg: float
    start_month: str
    is_active: bool
    created_at: datetime


class GoalUpdate(BaseModel):
    monthly_target_kg: float | None = Field(default=None, gt=0)
    start_month: str | None = None
    is_active: bool | None = None


class SummaryPayload(BaseModel):
    today_kg_co2e: float
    week_kg_co2e: float
    month_kg_co2e: float
    average_daily_kg_co2e: float
    active_goal: GoalRead | None = None
    goal_progress_percent: float = 0.0
    goal_remaining_kg: float = 0.0
    breakdown: list[dict] | None = None
    recommendations: list[str] | None = None
    recent_activities: list[ActivityRead] | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class TrendPoint(BaseModel):
    date: str
    total_kg_co2e: float


class RecommendationItem(BaseModel):
    title: str
    description: str
    priority: str
