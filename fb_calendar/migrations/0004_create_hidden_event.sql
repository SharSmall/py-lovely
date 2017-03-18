ALTER TABLE event ADD COLUMN hidden INTEGER DEFAULT 0;

INSERT INTO migrations (name) VALUES ('0004_create_hidden_event.sql');
