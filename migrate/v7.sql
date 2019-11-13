ALTER TABLE guilds ADD COLUMN starboard_id int;

CREATE TABLE IF NOT EXISTS starboards (
    starboard_id integer PRIMARY KEY AUTOINCREMENT,
    guild_id integer NOT NULL UNIQUE,
    channel_id integer NOT NULL UNIQUE,
    threshold integer NOT NULL DEFAULT 5,
    age integer NOT NULL DEFAULT 7,
    enabled integer DEFAULT 1
);

CREATE TABLE IF NOT EXISTS starboard_items (
    item_id integer PRIMARY KEY NOT NULL,
    original_id integer NOT NULL UNIQUE,
    guild_id integer NOT NULL,
    channel_id integer NOT NULL,
    author_id integer NOT NULL,
    starboard_id integer NOT NULL,
    visible integer NOT NULL DEFAULT 1
);
