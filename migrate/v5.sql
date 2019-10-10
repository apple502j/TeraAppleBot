CREATE TABLE IF NOT EXISTS votes (
    vote_id text PRIMARY KEY NOT NULL,
    created_by integer NOT NULL,
    created_at integer NOT NULL,
    expires integer NOT NULL,
    guild_id integer NOT NULL,
    title text NOT NULL,
    description text,
    yes_users text,
    no_users text
);
