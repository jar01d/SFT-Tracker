import sqlite3

# Connect to the database
db_path = 'db/srt.db'
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Insert values into achievement table
cursor.execute("""
INSERT INTO achievement (name) VALUES 
    ('Gold'),
    ('Silver'),
    ('Pass');
""")

# Insert values into instructor table
cursor.execute("""
INSERT INTO instructor (name) VALUES 
    ('Xing Mei');
""")

# Insert values into activity table
cursor.execute("""
INSERT INTO activity (name) VALUES 
    ('Run - Wingline'),
    ('Run - Yellow Cluster'),
    ('Gym - Wingline'),
    ('Basketball - Basketball Court');
""")

# Insert values into status table
cursor.execute("""
INSERT INTO status (name) VALUES 
    ('Pending Approval'),
    ('Ongoing'),
    ('Completed');
""")

cursor.execute("""
INSERT INTO 'group' (tele_id, name) VALUES 
    (NULL, 'No Group')
""")

# Commit changes and close the connection
connection.commit()
connection.close()

print("Tables populated successfully.")