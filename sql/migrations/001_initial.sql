-- Ticket 1, exercise 1
-- Create the pgvector extension and the core relational tables.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS teams (
    id BIGSERIAL PRIMARY KEY,
    nba_team_id BIGINT NOT NULL UNIQUE,
    abbreviation VARCHAR(10) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS players (
    id BIGSERIAL PRIMARY KEY,
    nba_player_id BIGINT NOT NULL UNIQUE,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    jersey_number INTEGER,
    position VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS games (
    id BIGSERIAL PRIMARY KEY,
    nba_game_id BIGINT NOT NULL UNIQUE,
    season VARCHAR(20) NOT NULL,
    game_date DATE NOT NULL,
    home_team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    away_team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (home_team_id <> away_team_id)
);

CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_games_season_date ON games(season, game_date);