from datetime import date, timedelta

from sqlalchemy import select

from app.carbon_calculator import calculate_emissions_kg
from app.database import Base, SessionLocal, engine
from app.models import Activity, Category, EmissionFactor, EmissionRecord

DEMO_ACTIVITY_COUNT = 232
DEMO_MARKER_PREFIX = "Demo data v6:"
DEMO_MARKER_QUERY = "Demo data%"

MONTHLY_ELECTRICITY_KWH = (35, 40, 45, 38, 50, 42, 55, 45, 30, 50, 40, 45)

TRANSPORT_ACTIVITIES = (
    ("Private car", (25, 30, 35, 40)),
    ("Private car", (25, 30, 35, 40)),
    ("Private car", (25, 30, 35, 40)),
    ("Two-wheeler", (15, 20, 25, 30)),
    ("Bus", (15, 20, 25, 30)),
    ("Delhi Metro", (15, 20, 25, 30)),
    ("Bicycle", (3, 5, 7, 9)),
    ("Walking", (2, 3, 4, 6)),
)

FOOD_ACTIVITIES = (
    ("Balanced Indian vegetarian diet (daily estimate)", 17),
    ("Vegan diet (daily estimate)", 5),
    ("Vegetarian diet (Italian daily estimate)", 5),
    ("Non-vegetarian diet (Italian daily estimate)", 5),
)

WASTE_ACTIVITIES = (
    "Organic waste (composting)",
    "Organic waste (landfilling)",
    "Organic waste (composting)",
    "Plastic waste (landfilling)",
    "Organic waste (composting)",
    "Organic waste (landfilling)",
    "Glass waste (landfilling)",
    "Organic waste (composting)",
    "Mixed e-waste / IT (specialised recycling)",
    "Organic waste (landfilling)",
    "Metal waste (landfilling)",
    "Organic waste (composting)",
)

WASTE_QUANTITIES = {
    "Organic waste (composting)": (0.5, 0.8, 1.0, 1.2),
    "Organic waste (landfilling)": (0.5, 0.8, 1.0),
    "Plastic waste (landfilling)": (0.3, 0.5),
    "Glass waste (landfilling)": (0.3, 0.5),
    "Metal waste (landfilling)": (0.2, 0.4),
    "Mixed e-waste / IT (specialised recycling)": (1.0, 2.0),
}

SHOPPING_ACTIVITIES = (
    ("Clothing item", 1.0, 18),
    ("Other consumer product", 1.0, 9),
    ("Clothing item", 1.0, 120),
    ("Other consumer product", 1.0, 75),
    ("Smartphone", 1.0, 320),
    ("Clothing item", 1.0, 235),
    ("Other consumer product", 1.0, 175),
    ("Other consumer product", 1.0, 285),
)


def _spread_days(count: int, first_day: int, last_day: int) -> list[int]:
    if count == 1:
        return [first_day]
    return [
        round(first_day + index * (last_day - first_day) / (count - 1))
        for index in range(count)
    ]


def build_demo_activities() -> tuple[dict, ...]:
    activities = []
    if len(MONTHLY_ELECTRICITY_KWH) != 12:
        raise RuntimeError("Demo electricity schedule must contain one entry per month.")

    for month_index, quantity in enumerate(MONTHLY_ELECTRICITY_KWH):
        activities.append({
            "marker": f"{DEMO_MARKER_PREFIX} electricity-month-{month_index + 1:02d}",
            "category": "Electricity",
            "activity_type": "Indian grid electricity (2026)",
            "quantity": float(quantity),
            "days_ago": 15 + month_index * 30,
        })

    food_types = [
        activity_type
        for activity_type, count in FOOD_ACTIVITIES
        for _ in range(count)
    ]
    for index, days_ago in enumerate(_spread_days(len(food_types), 8, 358)):
        activities.append({
            "marker": f"{DEMO_MARKER_PREFIX} food-{index + 1:02d}",
            "category": "Food",
            "activity_type": food_types[index],
            "quantity": 1.0,
            "days_ago": days_ago,
        })

    transport_days = _spread_days(168, 1, 354)
    for index, days_ago in enumerate(transport_days):
        activity_type, quantities = TRANSPORT_ACTIVITIES[index % len(TRANSPORT_ACTIVITIES)]
        activities.append({
            "marker": f"{DEMO_MARKER_PREFIX} transport-{index + 1:02d}",
            "category": "Transportation",
            "activity_type": activity_type,
            "quantity": float(quantities[(index // len(TRANSPORT_ACTIVITIES)) % len(quantities)]),
            "days_ago": days_ago,
        })

    for month_index, activity_type in enumerate(WASTE_ACTIVITIES):
        quantities = WASTE_QUANTITIES[activity_type]
        activities.append({
            "marker": f"{DEMO_MARKER_PREFIX} waste-{month_index + 1:02d}",
            "category": "Waste",
            "activity_type": activity_type,
            "quantity": quantities[month_index % len(quantities)],
            "days_ago": min(22 + month_index * 30, 359),
        })

    for index, (activity_type, quantity, days_ago) in enumerate(SHOPPING_ACTIVITIES):
        activities.append({
            "marker": f"{DEMO_MARKER_PREFIX} shopping-{index + 1:02d}",
            "category": "Shopping",
            "activity_type": activity_type,
            "quantity": quantity,
            "days_ago": days_ago,
        })

    if len(activities) != DEMO_ACTIVITY_COUNT:
        raise RuntimeError(
            f"Demo activity schedule contains {len(activities)} rows; "
            f"expected {DEMO_ACTIVITY_COUNT}."
        )
    return tuple(sorted(activities, key=lambda activity: (activity["days_ago"], activity["marker"])))


def seed_demo_data() -> tuple[int, int]:
    from main import seed_default_categories
    from app.carbon_calculator import seed_default_emission_factors

    Base.metadata.create_all(bind=engine)
    activities = build_demo_activities()
    markers = [activity["marker"] for activity in activities]
    added = 0
    replaced = 0

    with SessionLocal() as db:
        seed_default_categories(db)
        seed_default_emission_factors(db)
        existing_markers = [
            marker
            for (marker,) in db.query(Activity.notes)
            .filter(Activity.notes.like(DEMO_MARKER_QUERY))
            .all()
        ]
        if sorted(existing_markers) == sorted(markers):
            return 0, 0

        demo_activity_ids = select(Activity.id).where(
            Activity.notes.like(DEMO_MARKER_QUERY)
        )
        db.query(EmissionRecord).filter(
            EmissionRecord.activity_id.in_(demo_activity_ids)
        ).delete(synchronize_session=False)
        db.query(Activity).filter(Activity.notes.like(DEMO_MARKER_QUERY)).delete(
            synchronize_session=False
        )

        for sample in activities:
            category = db.query(Category).filter(Category.name == sample["category"]).one_or_none()
            factor = db.query(EmissionFactor).filter(
                EmissionFactor.category == sample["category"],
                EmissionFactor.activity_type == sample["activity_type"],
            ).one_or_none()
            if category is None or factor is None or factor.gas_basis != "CO2e":
                raise RuntimeError(
                    "Could not seed demo activity "
                    f"{sample['marker']!r}: its CO2e category or emission factor is missing."
                )

            activity_date = date.today() - timedelta(days=sample["days_ago"])
            emissions = calculate_emissions_kg(
                db,
                sample["category"],
                sample["activity_type"],
                sample["quantity"],
            )
            activity = Activity(
                category_id=category.id,
                activity_type=sample["activity_type"],
                quantity=sample["quantity"],
                unit=factor.unit,
                activity_date=activity_date,
                notes=sample["marker"],
                calculated_emissions_kg=emissions,
            )
            db.add(activity)
            db.flush()
            db.add(
                EmissionRecord(
                    activity_id=activity.id,
                    category=sample["category"],
                    activity_type=sample["activity_type"],
                    quantity=sample["quantity"],
                    unit=factor.unit,
                    co2e_kg=emissions,
                    recorded_date=activity_date,
                )
            )
            added += 1

        db.commit()
        replaced = len(existing_markers)

    return added, replaced


if __name__ == "__main__":
    added_count, replaced_count = seed_demo_data()
    activity_dates = [
        date.today() - timedelta(days=activity["days_ago"])
        for activity in build_demo_activities()
    ]
    if added_count:
        print(
            f"Demo data complete: added {added_count}, "
            f"replaced {replaced_count} prior demo samples."
        )
    else:
        print(f"Demo data already current ({DEMO_ACTIVITY_COUNT} activities).")
    print(f"Demo activity date range: {min(activity_dates)} to {max(activity_dates)}.")
