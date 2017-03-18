CREATE INDEX start_time_index ON event (start_time);
CREATE UNIQUE INDEX user_event_index ON user_event (fb_user_id, event_id);

INSERT INTO migrations (name) VALUES ('0001_create_event_index.sql');
