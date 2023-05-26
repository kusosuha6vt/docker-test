import time
import random

import psycopg2

db_name = 'database'
db_user = 'username'
db_pass = 'secret'
db_host = 'db'
db_port = '5432'

# Connecto to the database
db_string = 'postgresql://{}:{}@{}:{}/{}'.format(db_user, db_pass, db_host, db_port, db_name)
conn = psycopg2.connect(db_string)
cur = conn.cursor()

cur.execute('INSERT INTO numbers(number, timestamp) VALUES (1, 2)')
cur.execute('SELECT * FROM numbers')
print(cur.fetchone())
conn.commit()
cur.close()
conn.close()
