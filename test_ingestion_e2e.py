#!/usr/bin/env python
"""End-to-end ingestion test: normalize → insert → verify idempotency."""

import psycopg

from src.basketball_api.config import get_settings
from src.basketball_api.ingestion import normalize_payload
from src.basketball_api.insert import insert_normalized_payload


def count_rows(conn, table: str) -> int:
    """Count rows in a table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]


def get_row_counts(conn) -> dict:
    """Get row counts for all tables."""
    tables = ['teams', 'players', 'games', 'team_games', 'shots', 'play_by_play_actions']
    return {table: count_rows(conn, table) for table in tables}


def get_test_payload() -> dict:
    """Create a sample test payload."""
    return {
        "teams": [
            {
                "id": 1610612760,
                "abbreviation": "OKC",
                "full_name": "Oklahoma City Thunder",
                "city": "Oklahoma City",
                "nickname": "Thunder",
            },
            {
                "id": 1610612738,
                "abbreviation": "BOS",
                "full_name": "Boston Celtics",
                "city": "Boston",
                "nickname": "Celtics",
            },
        ],
        "players": [
            {
                "id": 2544,
                "team_id": 1610612760,
                "first_name": "Shai",
                "last_name": "Gilgeous-Alexander",
                "jersey_number": 2,
                "position": "G",
            },
            {
                "id": 2203999,
                "team_id": 1610612760,
                "first_name": "Jalen",
                "last_name": "Williams",
                "jersey_number": 8,
                "position": "F",
            }
        ],
        "games": [
            {
                "id": 21500001,
                "season": "2024-25",
                "date": "2024-10-22",
                "home_team_id": 1610612760,
                "away_team_id": 1610612738,
                "status": "Final",
            }
        ],
        "team_games": [
            {
                "game_id": 21500001,
                "team_id": 1610612760,
                "is_home": True,
                "score": 105,
            },
            {
                "game_id": 21500001,
                "team_id": 1610612738,
                "is_home": False,
                "score": 101,
            }
        ],
        "shots": [
            {
                "game_id": 21500001,
                "team_id": 1610612760,
                "player_id": 2544,
                "event_number": 1,
                "shot_made": True,
                "shot_type": "2PT",
                "shot_distance": 12.5,
                "period": 1,
                "clock": "12:00",
                "x_coordinate": 0.0,
                "y_coordinate": 0.0,
            }
        ],
    }


def run_ingestion(conn):
    """Run the full ingestion pipeline."""
    # Get test payload
    payload = get_test_payload()
    
    # Normalize
    print("Normalizing payload...")
    normalized = normalize_payload(payload)
    
    # Insert
    print("Inserting normalized data...")
    counts = insert_normalized_payload(conn, normalized)
    print(f"  Inserted: {counts}")
    
    conn.commit()
    print("Ingestion complete!")


def main():
    settings = get_settings()
    
    with psycopg.connect(settings.database_url) as conn:
        # First run
        print("\n=== FIRST RUN ===")
        counts_before = get_row_counts(conn)
        print(f"Row counts before: {counts_before}")
        
        run_ingestion(conn)
        
        counts_after_1 = get_row_counts(conn)
        print(f"Row counts after 1st run: {counts_after_1}")
        
        # Second run (idempotency check)
        print("\n=== SECOND RUN (Idempotency Check) ===")
        run_ingestion(conn)
        
        counts_after_2 = get_row_counts(conn)
        print(f"Row counts after 2nd run: {counts_after_2}")
        
        # Verify idempotency
        print("\n=== IDEMPOTENCY VERIFICATION ===")
        if counts_after_1 == counts_after_2:
            print("✓ PASS: Row counts unchanged (idempotent)")
        else:
            print("✗ FAIL: Row counts changed")
            for table in counts_after_1:
                if counts_after_1[table] != counts_after_2[table]:
                    print(f"  {table}: {counts_after_1[table]} → {counts_after_2[table]}")


if __name__ == "__main__":
    main()
