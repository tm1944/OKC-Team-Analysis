#!/usr/bin/env python
"""Database migration runner."""

from pathlib import Path

import psycopg

from src.basketball_api.config import get_settings
from src.basketball_api.migration_runner import run_migrations


def main() -> None:
    settings = get_settings()
    migrations_dir = Path(__file__).parent / "sql" / "migrations"

    with psycopg.connect(settings.database_url) as conn:
        applied = run_migrations(conn, migrations_dir)
        if applied:
            print(f"Applied migrations: {', '.join(applied)}")
        else:
            print("No new migrations to apply")


if __name__ == "__main__":
    main()
