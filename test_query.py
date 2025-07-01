import sqlite3

conn = sqlite3.connect('relationship.db')
cursor = conn.cursor()

# Example: Get all rows
cursor.execute('SELECT * FROM relationship_responses')
rows = cursor.fetchall()
for row in rows:
    print(row)

# Example: Get all columns
cursor.execute('PRAGMA table_info(relationship_responses)')
print(cursor.fetchall())

conn.close()
