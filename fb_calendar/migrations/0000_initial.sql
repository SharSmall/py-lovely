CREATE TABLE IF NOT EXISTS migrations (
  name VARCHAR(255),
  applied_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fb_user (
  fbid BIGINT PRIMARY KEY NOT NULL,
  access_token VARCHAR(255),
  expires_at BIGINT,
  grants VARCHAR(255) DEFAULT 'email,user_likes',
  total_friends BIGINT DEFAULT 0,
  created_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS friendship (
  fbid BIGINT NOT NULL,
  friend_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS event (
  page_id BIGINT,
  page_name VARCHAR(2048),
  name VARCHAR(2048),
  attending_count INTEGER,
  interested_count INTEGER,
  maybe_count INTEGER,
  noreply_count INTEGER,
  start_time BIGINT,
  end_time BIGINT,
  picture_url VARCHAR(2048),
  id BIGINT PRIMARY KEY NOT NULL,
  description TEXT,
  ticket_uri VARCHAR(4096),
  place VARCHAR(1024),
  created_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS user_event (
  event_id BIGINT,
  fb_user_id BIGINT,
  created_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS page (
  id BIGINT PRIMARY KEY NOT NULL,
  name VARCHAR(2048),
  place_type VARCHAR(255),
  link VARCHAR(4096),
  created_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
  most_recent_user_id BIGINT,
  token_expires_at BIGINT
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = EXTRACT(EPOCH FROM NOW());
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_page_updated_at BEFORE UPDATE ON page FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_event_updated_at BEFORE UPDATE ON event FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER fb_user_updated_at BEFORE UPDATE ON fb_user FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_user_event_updated_at BEFORE UPDATE ON user_event FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

INSERT INTO migrations (name) VALUES ('0000_initial.sql');
