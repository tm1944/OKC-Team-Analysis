"""Shared database feature queries for the shot-make model."""

# Keep this query as the single structured-data source for both model training
# and API-time feature lookup. The lone parameter is the database player ID.
SHOT_FEATURES_SQL = """
SELECT
    s.player_id,
    p.first_name || ' ' || p.last_name AS player_name,
    s.shot_made,
    s.shot_distance,
    s.shot_type AS shot_zone,
    s.period,
    (
        SPLIT_PART(s.clock, ':', 1)::INTEGER * 60
        + SPLIT_PART(s.clock, ':', 2)::INTEGER
    ) AS seconds_remaining,
    tg.is_home,
    s.game_id,
    g.game_date
FROM shots AS s
JOIN players AS p ON p.id = s.player_id
JOIN games AS g ON g.id = s.game_id
JOIN team_games AS tg ON tg.game_id = s.game_id AND tg.team_id = s.team_id
WHERE s.player_id = %s
ORDER BY g.game_date ASC, s.id ASC
"""


# Training spans all available players in a season, while the player-scoped
# query above is retained for later API analytics.
SHOT_FEATURES_FOR_SEASON_SQL = SHOT_FEATURES_SQL.replace(
    "WHERE s.player_id = %s",
    "WHERE g.season = %s",
)
