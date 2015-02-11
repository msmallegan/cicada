"""
Naive view of data.

"""
from ast import literal_eval
from collections import OrderedDict

import datetime
import sqlite3
import cgi
import json

import os
from os.path import expanduser
HOME = expanduser("~")

# Note: Convert to datetime via:
#    datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')

# Note: If frequency_in is '--' in HTML, then it is saved
#    into database as null, which is exported to Python as None.

dbname = os.path.join(HOME, 'webapps/basic/cicada/frequencies.sqlite3')

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
    output = json.dumps(x)
    headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
    ]
    return headers, output

def get_instructions():
    statement = '''SELECT value from admin where key = "pause"'''
    db = sqlite3.connect(dbname)
    c = db.cursor()
    c.execute(statement)
    pause = c.fetchone()[0]
    if pause == "1" or pause == "true":
        pause = True
    else:
        pause = False
    x = {'pause': pause}
    output = json.dumps(x)
    headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
    ]
    return headers, output

def set_instructions(instructions):
    known_keys = ['pause']

    db = sqlite3.connect(dbname)
    db.row_factory = list_factory
    c = db.cursor()

    pause = '''UPDATE admin set value = "1" where key = "pause"'''
    unpause = '''UPDATE admin set value = "0" where key = "pause"'''

    if instructions["pause"] == "1" or instructions["pause"] == "true":
        c.execute(pause)
    else:
        c.execute(unpause)
    db.commit()

    output = ''
    headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
    ]
    return headers, output



def rows_since(session, row_id):
    statement = '''SELECT * FROM frequencies where session = ? and id > ?
                   ORDER BY id DESC'''

    db = sqlite3.connect(dbname)
    # To send less bytes, just use the list.
    #db.row_factory = dict_factory
    db.row_factory = list_factory
    c = db.cursor()
    c.execute(statement, (session, row_id))
    rows = c.fetchall()
    output = json.dumps(rows)
    db.close()

    headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
    ]
    return headers, output


def last_30():
    db = sqlite3.connect(dbname)
    c = db.cursor()
    c.execute('SELECT * FROM frequencies ORDER BY id DESC LIMIT 30;')

    output = ["""
    id, session, location, date sent, date received, frequency_in, frequency_out
    """]
    for row in c:
        output.append(str(row))
    db.close()

    output = '\n'.join(output)
    headers = [
        ('Content-Length', str(len(output))),
        ('Content-Type', 'text/plain'),
    ]
    return headers, output

def getvalue(item):
    try:
        # GET
        x  = item[0]
    except TypeError:
        # POST
        x = item.value
    return x

def application(environ, start_response):

    if environ['REQUEST_METHOD'] == 'POST':
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        post = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=post_env,
            keep_blank_values=True
        )
        form = post
    elif environ['QUERY_STRING']:
        form = cgi.parse_qs(environ['QUERY_STRING'])
        form['REQUEST_METHOD'] = 'GET'
    else:
        form = {}

    #output = str(form)
    #headers = [
    #    ('Content-Length', str(len(output))),
    #    ('Content-Type', 'text/plain'),
    #    ('Access-Control-Allow-Origin', '*'),
    #]

    try:
        session = form['session']
    except KeyError:
        headers, output = last_30()
    else:
        session = getvalue(session)

        if session == 'admin':
            # Send out instructions to clients.
            try:
                # hardcode "pause" for now
                pause = form['pause']
            except KeyError:
                headers, output = get_instructions()
            else:
                pause = getvalue(pause)
                instructions = {'pause': pause}
                set_instructions(instructions)
                headers, output = get_instructions()
        else:
            try:
                row_id = form['row_id']
            except KeyError:
                headers, output = last_30()
            else:
                row_id = getvalue(row_id)
                if row_id == 'last':
                    headers, output = json_last_row()
                else:
                    row_id = int(row_id)
                    headers, output = rows_since(session, row_id)

    start_response('200 OK', headers)

    return [bytes(output, 'utf-8')]