#!/usr/local/bin/python2.7
"""
Naive view of data.

"""
from __future__ import print_function

from ast import literal_eval
from collections import OrderedDict

import datetime
import sqlite3
import cgi
import json

# Note: Convert to datetime via:
#    datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')

# Note: If frequency_in is '--' in HTML, then it is saved
#    into database as null, which is exported to Python as None.

dbname = 'frequencies.sqlite3'

def dict_factory(cursor, row):
    d = OrderedDict()
    for idx, col in enumerate(cursor.description):
        if idx == 2:
            # Convert "[1,2]" to [1,2]
            val = literal_eval(row[idx])
        else:
            val = row[idx]
        d[col[0]] = val
    return d

def list_factory(cursor, row):
    d = []
    for idx, col in enumerate(cursor.description):
        if idx == 2:
            # Convert "[1,2]" to [1,2]
            val = literal_eval(row[idx])
        else:
            val = row[idx]
        d.append(val)
    return d

def last_row():
    statement = '''SELECT id FROM frequencies ORDER BY id DESC limit 1'''
    db = sqlite3.connect(dbname)
    c = db.cursor()
    c.execute(statement)
    row_id = c.fetchone()[0]
    return row_id

def json_last_row():
    x = {'last_row': last_row()}
    print("Content-type: application/json")
    print("Access-Control-Allow-Origin: *\n")
    print(json.dumps(x))

def rows_since(session, row_id):
    statement = '''SELECT * FROM frequencies where session = ? and id > ?
                   ORDER BY id DESC'''

    db = sqlite3.connect(dbname)
    # To send less bytes, just use the list.
    #db.row_factory = dict_factory
    db.row_factory = list_factory
    c = db.cursor()
    c.execute(statement, (session, row_id))
    print("Content-type: application/json")
    print("Access-Control-Allow-Origin: *\n")
    rows = c.fetchall()
    print(json.dumps(rows))
    db.close()

def last_30():
    db = sqlite3.connect(dbname)
    c = db.cursor()
    c.execute('SELECT * FROM frequencies ORDER BY id DESC LIMIT 30;')

    print("Content-type: text/plain\n\n")
    print("""
    id, session, location, date sent, date received, frequency_in, frequency_out
    """)
    for row in c:
        print(row)
    db.close()

def main():
    form = cgi.FieldStorage()
    try:
        session = form['session']
    except KeyError:
        last_30()
    else:
        session = session.value
        row_id = form['row_id'].value
        if row_id == 'last':
            json_last_row()
        else:
            row_id = int(row_id)
            rows_since(session, row_id)

if __name__ == '__main__':
    main()
