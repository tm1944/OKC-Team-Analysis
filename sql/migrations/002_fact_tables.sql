-- Add the per-game fact tables for team participation, shots,
-- play-by-play actions, and pipeline ingestion tracking.

CREATE TABLE IF NOT EXISTS team_games (
    id BIGSERIAL PRIMARY KEY,
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    is_home BOOLEAN NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game_id, team_id)
);

CREATE TABLE IF NOT EXISTS shots (
    id BIGSERIAL PRIMARY KEY,
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    player_id BIGINT NOT NULL REFERENCES players(id) ON DELETE RESTRICT,
    event_number INTEGER NOT NULL,
    shot_made BOOLEAN NOT NULL,
    shot_type VARCHAR(50),
    shot_distance NUMERIC(5, 2),
    period INTEGER NOT NULL CHECK (period BETWEEN 1 AND 5),
    clock VARCHAR(10),
    x_coordinate NUMERIC(6, 2),
    y_coordinate NUMERIC(6, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game_id, event_number)
);

CREATE TABLE IF NOT EXISTS play_by_play_actions (
    id BIGSERIAL PRIMARY KEY,
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id BIGINT REFERENCES teams(id) ON DELETE RESTRICT,
    player_id BIGINT REFERENCES players(id) ON DELETE RESTRICT,
    event_number INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    period INTEGER NOT NULL CHECK (period BETWEEN 1 AND 5),
    clock VARCHAR(10),
    score_text VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game_id, event_number)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'success', 'failed', 'partial')),
    source VARCHAR(30) NOT NULL,
    notes TEXT,
    records_processed INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_team_games_game_id ON team_games(game_id);
CREATE INDEX IF NOT EXISTS idx_team_games_team_id ON team_games(team_id);
CREATE INDEX IF NOT EXISTS idx_shots_game_id ON shots(game_id);
CREATE INDEX IF NOT EXISTS idx_shots_player_id ON shots(player_id);
CREATE INDEX IF NOT EXISTS idx_play_by_play_game_id ON play_by_play_actions(game_id);
CREATE INDEX IF NOT EXISTS idx_play_by_play_player_id ON play_by_play_actions(player_id);
