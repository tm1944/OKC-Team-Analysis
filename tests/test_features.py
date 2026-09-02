from basketball_api.features import SHOT_FEATURES_SQL


def test_shot_features_query_contains_required_fields_and_joins() -> None:
    query = " ".join(SHOT_FEATURES_SQL.lower().split())

    for field in (
        "s.player_id",
        "player_name",
        "s.shot_made",
        "s.shot_distance",
        "shot_zone",
        "s.period",
        "seconds_remaining",
        "tg.is_home",
        "s.game_id",
        "g.game_date",
    ):
        assert field in query

    for join in ("join players", "join games", "join team_games"):
        assert join in query

    assert "where s.player_id = %s" in query
    assert "order by g.game_date asc, s.id asc" in query
