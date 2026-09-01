from __future__ import annotations

from pathlib import Path

from basketball_api.migration_runner import get_migration_files, run_migrations


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.rows: list[tuple[str]] = []

    def execute(self, query: str, params: tuple | None = None) -> None:
        self.executed.append(query)
        if "INSERT INTO schema_migrations" in query:
            self.rows.append((params[0],))

    def fetchall(self) -> list[tuple[str]]:
        return self.rows


class FakeConnection:
    def __init__(self) -> None:
        self.cursor = FakeCursor()
        self.transactions: list[str] = []

    def execute(self, query: str, params: tuple | None = None) -> None:
        self.cursor.execute(query, params)

    def transaction(self):
        class Tx:
            def __enter__(self) -> None:
                pass

            def __exit__(self, exc_type, exc, tb) -> None:
                pass

        return Tx()


def test_get_migration_files_orders_sql_files(tmp_path: Path) -> None:
    (tmp_path / "010_later.sql").write_text("-- later")
    (tmp_path / "001_first.sql").write_text("-- first")
    (tmp_path / "notes.txt").write_text("ignore me")

    files = get_migration_files(tmp_path)

    assert [p.name for p in files] == ["001_first.sql", "010_later.sql"]


def test_run_migrations_skips_already_applied(tmp_path: Path) -> None:
    sql1 = tmp_path / "001_initial.sql"
    sql1.write_text("CREATE TABLE test (id INT);")
    sql2 = tmp_path / "002_fact_tables.sql"
    sql2.write_text("CREATE TABLE test2 (id INT);")

    conn = FakeConnection()
    applied = run_migrations(conn, tmp_path)

    assert applied == ["001_initial", "002_fact_tables"]
    assert any("CREATE TABLE test" in q for q in conn.cursor.executed)
    assert any("CREATE TABLE test2" in q for q in conn.cursor.executed)
