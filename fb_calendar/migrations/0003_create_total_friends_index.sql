CREATE INDEX fb_user_total_friends_index ON fb_user (total_friends);

INSERT INTO migrations (name) VALUES ('0003_create_total_friends_index.sql');
