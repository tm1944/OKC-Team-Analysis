from basketball_api.planner import plan_question


def test_recent_rim_question_maps_to_zone_and_default_window() -> None:
    plan = plan_question("How effective is he near the rim recently?", None)

    assert plan.shot_zone == "Restricted Area"
    assert plan.default_last_n_games == 10


def test_coverage_question_is_flagged_as_a_limitation() -> None:
    assert plan_question("How does he perform against drop coverage?", 5).coverage_question
