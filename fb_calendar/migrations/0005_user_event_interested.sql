ALTER TABLE user_event ADD COLUMN interested INTEGER DEFAULT 0;

INSERT INTO migrations (name) VALUES ('0005_user_event_interested.sql');
