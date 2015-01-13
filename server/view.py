#!/usr/local/bin/python2.7
"""
Naive view of data.

"""
from __future__ import print_function

import datetime
import sqlite3

db = sqlite3.connect('frequencies.sqlite3')
c = db.cursor()
c.execute('SELECT * FROM frequencies ORDER BY id DESC LIMIT 30;')

print("Content-type: text/plain\n\n")
print("""
id, session, location, date sent, date received, frequency_in, frequency_out
""")
for row in c:
    print(row)

# Note: Convert to datetime via:
#    datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')

# Note: If frequency_in is '--' in HTML, then it is saved
#    into database as null, which is exported to Python as None.

db.close()

