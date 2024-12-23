-- Create achievement table (to manually populate)
CREATE TABLE IF NOT EXISTS achievement (
    achievement_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Create status table (to manually populate)
CREATE TABLE IF NOT EXISTS 'status' (
    status_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Create activity table (to manually populate)
CREATE TABLE IF NOT EXISTS activity (
    activity_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Create instructor table (to manually populate)
CREATE TABLE IF NOT EXISTS instructor (
    instructor_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Create cadet table
CREATE TABLE IF NOT EXISTS cadet (
    cadet_id INTEGER PRIMARY KEY,
    tele_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    name TEXT NOT NULL UNIQUE,
    achievement_id INTEGER,
    FOREIGN KEY (achievement_id) REFERENCES achievement (achievement_id) ON DELETE CASCADE
);

-- Create group table
CREATE TABLE IF NOT EXISTS 'group' (
    group_id INTEGER PRIMARY KEY,
    tele_id INTEGER NOT NULL,
    name TEXT,
    UNIQUE (tele_id, name)
    FOREIGN KEY (achievement_id) REFERENCES achievement (achievement_id) ON DELETE CASCADE
);

-- Create cadet_group table
CREATE TABLE IF NOT EXISTS cadet_group (
	cadet_group_id INTEGER PRIMARY KEY
    cadet_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
	UNIQUE (cadet_id,group_id),
    FOREIGN KEY (cadet_id) REFERENCES cadet (cadet_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES 'group' (group_id) ON DELETE CASCADE
);



-- Create sft_info table
CREATE TABLE IF NOT EXISTS sft_info (
    sft_id INTEGER PRIMARY KEY,
    cadet_id INTEGER,
    activity_id INTEGER,
    datetime_in TEXT NOT NULL, --(YYYY-MM-DD HH:MM:SS)
    datetime_out TEXT, 
    status_id INTEGER,
    FOREIGN KEY (cadet_id) REFERENCES cadet (cadet_id) ON DELETE CASCADE,
    FOREIGN KEY (activity_id) REFERENCES activity (activity_id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES status (status_id) ON DELETE CASCADE
);

