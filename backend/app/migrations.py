from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate_legacy_account_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    legacy_tables = {
        table
        for table in ("activities", "goals", "emission_records")
        if table in tables
        and any(column["name"] == "user_id" for column in inspector.get_columns(table))
    }
    if not legacy_tables:
        return

    if engine.dialect.name == "sqlite":
        _migrate_sqlite(engine, legacy_tables, "users" in tables)
        return
    if engine.dialect.name in {"mysql", "mariadb"}:
        _migrate_mysql(engine, inspector, legacy_tables, tables)
        return

    raise RuntimeError(
        f"Cannot migrate legacy account columns for database dialect {engine.dialect.name!r}"
    )


def migrate_factor_metadata(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    columns_to_add = {
        "emission_factors": {
            "source_url": "VARCHAR(500)",
            "geography": "VARCHAR(100)",
            "gas_basis": "VARCHAR(20)",
            "methodology": "VARCHAR(100)",
            "verification_status": "VARCHAR(50)",
            "notes": "TEXT",
        },
    }
    with engine.begin() as connection:
        for table, columns in columns_to_add.items():
            if table not in tables:
                continue
            existing_columns = {column["name"] for column in inspect(connection).get_columns(table)}
            for column, sql_type in columns.items():
                if column not in existing_columns:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"
                    )


def migrate_co2e_only(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if engine.dialect.name not in {"sqlite", "mysql", "mariadb", "postgresql"}:
        raise RuntimeError(
            f"Cannot remove obsolete emissions-basis columns for database "
            f"dialect {engine.dialect.name!r}"
        )

    with engine.begin() as connection:
        columns_to_drop = []
        for table in ("activities", "emission_records"):
            if table not in tables:
                continue
            columns = {column["name"] for column in inspect(connection).get_columns(table)}
            if "emissions_basis" not in columns:
                continue
            other_basis_count = connection.exec_driver_sql(
                f"SELECT COUNT(*) FROM {table} "
                "WHERE emissions_basis IS NULL OR emissions_basis != 'CO2e'"
            ).scalar_one()
            if other_basis_count:
                raise RuntimeError(
                    f"Cannot remove the emissions basis from {table}: "
                    f"{other_basis_count} saved row(s) are not CO2e. "
                    "Recalculate or archive those entries before restarting EcoMeter."
                )
            columns_to_drop.append(table)

        if engine.dialect.name == "sqlite":
            sqlite_version = tuple(
                int(part) for part in connection.exec_driver_sql("SELECT sqlite_version()").scalar_one().split(".")
            )
            if sqlite_version < (3, 35, 0) and columns_to_drop:
                raise RuntimeError(
                    "Removing obsolete emissions-basis columns requires SQLite 3.35.0 or newer."
                )

        for table in columns_to_drop:
            connection.exec_driver_sql(
                f"ALTER TABLE {table} DROP COLUMN emissions_basis"
            )


def _migrate_sqlite(engine: Engine, legacy_tables: set[str], has_users_table: bool) -> None:
    definitions = {
        "activities": (
            """
            CREATE TABLE activities_single_user (
                id INTEGER NOT NULL PRIMARY KEY,
                category_id INTEGER NOT NULL,
                activity_type VARCHAR(100) NOT NULL,
                quantity FLOAT NOT NULL,
                unit VARCHAR(50) NOT NULL,
                activity_date DATE NOT NULL,
                notes TEXT,
                calculated_emissions_kg FLOAT NOT NULL DEFAULT 0.0,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(category_id) REFERENCES categories (id)
            )
            """,
            "id, category_id, activity_type, quantity, unit, activity_date, "
            "notes, calculated_emissions_kg, created_at",
        ),
        "goals": (
            """
            CREATE TABLE goals_single_user (
                id INTEGER NOT NULL PRIMARY KEY,
                monthly_target_kg FLOAT NOT NULL,
                start_month VARCHAR(10) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL
            )
            """,
            "id, monthly_target_kg, start_month, is_active, created_at",
        ),
        "emission_records": (
            """
            CREATE TABLE emission_records_single_user (
                id INTEGER NOT NULL PRIMARY KEY,
                activity_id INTEGER NOT NULL,
                category VARCHAR(50) NOT NULL,
                activity_type VARCHAR(100) NOT NULL,
                quantity FLOAT NOT NULL,
                unit VARCHAR(50) NOT NULL,
                co2e_kg FLOAT NOT NULL,
                recorded_date DATE NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE
            )
            """,
            "id, activity_id, category, activity_type, quantity, unit, "
            "co2e_kg, recorded_date, created_at",
        ),
    }
    replacement_names = {
        "activities": "activities_single_user",
        "goals": "goals_single_user",
        "emission_records": "emission_records_single_user",
    }

    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
        try:
            with connection.begin():
                for table in ("activities", "goals", "emission_records"):
                    if table not in legacy_tables:
                        continue
                    create_sql, columns = definitions[table]
                    replacement = replacement_names[table]
                    connection.exec_driver_sql(create_sql)
                    connection.exec_driver_sql(
                        f"INSERT INTO {replacement} ({columns}) "
                        f"SELECT {columns} FROM {table}"
                    )

                for table in ("emission_records", "activities", "goals"):
                    if table in legacy_tables:
                        connection.exec_driver_sql(f"DROP TABLE {table}")
                if has_users_table:
                    connection.exec_driver_sql("DROP TABLE users")

                for table in ("activities", "goals", "emission_records"):
                    if table in legacy_tables:
                        connection.exec_driver_sql(
                            f"ALTER TABLE {replacement_names[table]} RENAME TO {table}"
                        )
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()


def _migrate_mysql(
    engine: Engine,
    inspector,
    legacy_tables: set[str],
    tables: set[str],
) -> None:
    preparer = engine.dialect.identifier_preparer
    with engine.begin() as connection:
        for table in legacy_tables:
            quoted_table = preparer.quote(table)
            for foreign_key in inspector.get_foreign_keys(table):
                if "user_id" not in foreign_key.get("constrained_columns", []):
                    continue
                name = foreign_key.get("name")
                if name:
                    connection.execute(
                        text(
                            f"ALTER TABLE {quoted_table} DROP FOREIGN KEY "
                            f"{preparer.quote(name)}"
                        )
                    )

        for table in legacy_tables:
            connection.execute(
                text(f"ALTER TABLE {preparer.quote(table)} DROP COLUMN user_id")
            )
        if "users" in tables:
            connection.execute(text(f"DROP TABLE {preparer.quote('users')}"))
