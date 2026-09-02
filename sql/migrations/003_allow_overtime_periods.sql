ALTER TABLE shots DROP CONSTRAINT IF EXISTS shots_period_check;
ALTER TABLE shots ADD CONSTRAINT shots_period_check CHECK (period BETWEEN 1 AND 10);

ALTER TABLE play_by_play_actions DROP CONSTRAINT IF EXISTS play_by_play_actions_period_check;
ALTER TABLE play_by_play_actions
    ADD CONSTRAINT play_by_play_actions_period_check CHECK (period BETWEEN 1 AND 10);

