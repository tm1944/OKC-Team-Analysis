from __future__ import annotations

from pathlib import Path
from typing import Any


def get_migration_files(migrations_dir: str | Path) -> list[Path]:
    directory = Path(migrations_dir)
    if not directory.exists():
        return []

    return sorted(
        [path for path in directory.iterdir() if path.suffix == ".sql"],
        key=lambda path: path.name,
    )


def _ensure_schema_migrations_table(conn: Any) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def _applied_versions(conn: Any) -> set[str]:
    conn.execute("SELECT version FROM schema_migrations")
    rows = conn.cursor.fetchall()
    return {row[0] for row in rows}


def run_migrations(conn: Any, migrations_dir: str | Path) -> list[str]:
    _ensure_schema_migrations_table(conn)

    applied = _applied_versions(conn)
    applied_versions: list[str] = []

    for migration_file in get_migration_files(migrations_dir):
		#001_initial.sql -> 001_initial
        version = migration_file.stem
        if version in applied:
            continue

        sql = migration_file.read_text(encoding="utf-8")
        with conn.transaction():
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,),
            )

        applied_versions.append(version)

    return applied_versions
