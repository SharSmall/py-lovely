CREATE UNIQUE INDEX fbid_friend_id_index ON friendship (fbid, friend_id);

INSERT INTO migrations (name) VALUES ('0002_create_friend_index.sql');
