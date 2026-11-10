from sqlalchemy.orm import Session

from .emission_factor_data import DEFAULT_FACTORS
from .models import EmissionFactor

RETIRED_FACTOR_KEYS = {
    ("Electricity", "Indian grid electricity (FY 2023-24)"),
    ("Electricity", "Indian grid electricity (FY 2024-25)"),
    ("Electricity", "Indian grid electricity (FY 2025-26)"),
    ("Transportation", "Car"),
    ("Transportation", "Delhi Metro (Method 1)"),
    ("Transportation", "Delhi Metro (Method 2)"),
    ("Food", "Balanced vegetarian adult diet (daily estimate)"),
}

LEGACY_FACTOR_KEYS = {
    ("Transportation", "Car"),
    ("Transportation", "Motorcycle"),
    ("Transportation", "Bus"),
    ("Transportation", "Metro"),
    ("Transportation", "Train"),
    ("Transportation", "Bicycle"),
    ("Transportation", "Walking"),
    ("Electricity", "Electricity consumption"),
    ("Food", "Vegetarian meal"),
    ("Food", "Non-vegetarian meal"),
    ("Food", "Vegan meal"),
    ("Shopping", "Clothing"),
    ("Shopping", "Electronics"),
    ("Shopping", "Other purchases"),
    ("Waste", "General waste"),
    ("Waste", "Recycled waste"),
    ("Waste", "Organic waste"),
}
LEGACY_FACTOR_SOURCES = {
    "Illustrative India campus estimate; replace with verified local factors.",
    "Zero direct emissions for active travel.",
    "Illustrative India grid coefficient; replace with verified local factor.",
    "Illustrative estimate for a demo app.",
    "Central Electricity Authority, CO2 Baseline Database, Version 22.0",
    "TERI, Emission Saving Made by a Passenger by Choosing to Travel by Delhi Metro",
    "Direct operational boundary",
    "Pathak et al., Carbon Footprints of Indian Food Items",
    "MoEFCC, Low Carbon Lifestyles: Right Choices for Our Planet",
    "Joint Research Centre (JRC), publication JRC129957",
    "EcoMeter illustrative assumption; references TERI and ITF",
    "EcoMeter illustrative assumption",
}


def seed_default_emission_factors(db: Session) -> None:
    for row in db.query(EmissionFactor).all():
        if (
            (row.category, row.activity_type) in RETIRED_FACTOR_KEYS
            and row.source in LEGACY_FACTOR_SOURCES
        ):
            db.delete(row)

    legacy_rows = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.source.in_(LEGACY_FACTOR_SOURCES))
        .all()
    )
    for row in legacy_rows:
        if (row.category, row.activity_type) in LEGACY_FACTOR_KEYS:
            db.delete(row)
    db.flush()

    existing_rows = {
        (row.category, row.activity_type): row
        for row in db.query(EmissionFactor).all()
    }
    for factor in DEFAULT_FACTORS:
        key = (factor["category"], factor["activity_type"])
        existing = existing_rows.get(key)
        if existing is None:
            db.add(EmissionFactor(**factor, is_verified=False))
        elif existing.source in LEGACY_FACTOR_SOURCES and not existing.is_verified:
            for field, value in factor.items():
                setattr(existing, field, value)
    db.commit()


def get_emission_factor(db: Session, category: str, activity_type: str) -> EmissionFactor:
    factor = (
        db.query(EmissionFactor)
        .filter(
            EmissionFactor.category == category,
            EmissionFactor.activity_type == activity_type,
        )
        .first()
    )
    if not factor:
        raise ValueError(f"No emission factor found for {category} / {activity_type}")
    return factor


def calculate_emissions_kg(db: Session, category: str, activity_type: str, quantity: float) -> float:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    factor = get_emission_factor(db, category, activity_type)
    return round(quantity * factor.emission_factor, 6)


def normalize_category_name(name: str) -> str:
    names = {
        "transportation": "Transportation",
        "electricity": "Electricity",
        "food": "Food",
        "shopping": "Shopping",
        "waste": "Waste",
    }
    return names.get(name.lower(), name.title())
