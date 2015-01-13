#!/usr/local/bin/python2.7
"""
Naive view of data.

"""
from __future__ import print_function

import sqlite3

db = sqlite3.connect('frequencies.sqlite3')
c = db.cursor()
c.execute('SELECT * FROM frequencies;')

print("Content-type: text/plain\n\n")
print("id, session, location, date sent, date received, frequency")
for row in c:
    print(row)
db.close()

