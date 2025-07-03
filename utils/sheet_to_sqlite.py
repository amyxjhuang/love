import sqlite3
from format_sheet import responses  # Assumes format_sheet.py defines 'responses' at the top level

# Connect to SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect('relationship.db')
cursor = conn.cursor()

# Create table (run once)
cursor.execute('''
CREATE TABLE IF NOT EXISTS relationship_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    user TEXT,
    still_like TEXT,
    crash_out TEXT,
    stress_level INTEGER,
    argued TEXT,
    period TEXT,
    select_all_true TEXT,
    relationship_strength INTEGER,
    coitus TEXT,
    coitus_quality TEXT,
    hangout TEXT,
    long_distance TEXT,
    check_all_true TEXT,
    day_for TEXT,
    fellatio TEXT,
    jealousy TEXT,
    good_memory TEXT,
    worries TEXT,
    anything_else TEXT
)
''')

# Insert data
for row in responses:
    cursor.execute('''
        INSERT INTO relationship_responses (
            timestamp, still_like, crash_out, stress_level, argued, period,
            select_all_true, relationship_strength, coitus, coitus_quality,
            hangout, long_distance, check_all_true, day_for, user,
            fellatio, jealousy, good_memory, worries, anything_else
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row.get('Timestamp'),
        row.get('Do you still like me? '),
        row.get('Did you have any crash outs about us? \n\nSomething counts as a crash out if you spent >30 minutes worrying about the relationship, or had a bad thought that lasted multiple days. '),
        row.get('How stressed are you about things outside of our relationship? '),
        row.get('Did we argue? \n\nSomething counts as an argument if one party felt anger about something, and brought it up, and it was not immediately resolved. '),
        row.get('Was Amy on her period?'),
        ', '.join(row.get('Select all that you feel is true ', [])) if isinstance(row.get('Select all that you feel is true '), list) else row.get('Select all that you feel is true '),
        row.get('How strong do you think our relationship is?'),
        row.get('Did we have coitus during this hangout?'),
        row.get('If coitus took place, how good was the coitus for you?'),
        row.get('Did you hang out (in real life)? '),
        row.get('Are you long distance right now?'),
        ', '.join(row.get('Check all that are true for this hangout.', [])) if isinstance(row.get('Check all that are true for this hangout.'), list) else row.get('Check all that are true for this hangout.'),
        row.get('What day is this for? '),
        row.get('Who is filling this out right now.'),
        row.get('Did we do fellatio during this hangout?'),
        row.get('If you experienced jealousy recently, what was it from?\n\nOnly fill this out once per jealous event. '),
        row.get("What's a good memory from this hangout (or relationship)? "),
        row.get("What's something you're worried about? "),
        row.get('Anything else to note?')
    ))

conn.commit()
conn.close()

print('Data loaded into relationship.db')
