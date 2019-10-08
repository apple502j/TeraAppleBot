CREATE TABLE IF NOT EXISTS pending_delete (
    original_id integer PRIMARY KEY NOT NULL,
    channel_id integer NOT NULL,
    target_id integer NOT NULL
);
