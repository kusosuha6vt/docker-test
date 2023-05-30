CREATE TYPE ship_type AS ENUM ('cruiser', 'icebreaker', 'ferry', 'fishing boat');

CREATE TABLE ships(
    id INT PRIMARY KEY,
    name text NOT NULL,
    year INT NOT NULL,
    flag text NOT NULL,
    type ship_type NOT NULL,
    dock_id uuid
);

CREATE TABLE docks(
    id uuid PRIMARY KEY,
    name TEXT NOT NULL,
    latitude NUMERIC NOT NULL,
    longitude NUMERIC NOT NULL,
    max_ships INT NOT NULL,
    cur_ships INT NOT NULL
);