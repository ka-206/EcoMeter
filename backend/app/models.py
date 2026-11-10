from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    activities = relationship("Activity", back_populates="category")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    activity_type = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    activity_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    calculated_emissions_kg = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    category = relationship("Category", back_populates="activities")
    emission_records = relationship("EmissionRecord", back_populates="activity", cascade="all, delete-orphan")


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    activity_type = Column(String(100), nullable=False)
    emission_factor = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    source = Column(String(255), nullable=False)
    reference_year = Column(Integer, nullable=False, default=2024)
    is_verified = Column(Boolean, nullable=False, default=False)
    source_url = Column(String(500), nullable=True)
    geography = Column(String(100), nullable=True)
    gas_basis = Column(String(20), nullable=True)
    methodology = Column(String(100), nullable=True)
    verification_status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = ({"sqlite_autoincrement": True},)


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    monthly_target_kg = Column(Float, nullable=False)
    start_month = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class EmissionRecord(Base):
    __tablename__ = "emission_records"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    activity_type = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    co2e_kg = Column(Float, nullable=False)
    recorded_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    activity = relationship("Activity", back_populates="emission_records")
