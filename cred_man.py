#
#
# Copyright (c) 2013, theZacAttacks
#
# Manages the database filled with user information
#

import sqlite3
from twitter import Api
from os import path, remove
from platform import system
from base64 import b64encode, b64decode

WINDOWS_PATH = path.expanduser('~\AppData\\Roaming\\tcler.db')
UNIX_PATH = path.expanduser('~/.tcler.db')
DB_CUR = None

global TABLE_CREATED
TABLE_CREATED = False


# creates the table if the table doesn't exist
def createTable():
    DB_CUR.execute('''CREATE TABLE creds(id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_name varchar(100),
    key varchar(150),
    secret varchar(150))''')
    DB_CUR.commit()
    global TABLE_CREATED
    TABLE_CREATED = True


# gets the status of the table (whether or not it's created)
def getTableStatus():
    return TABLE_CREATED


# adds a user to the database
def addUser(key, secret, name):
    try:
        if name is not None:
            DB_CUR.execute('''INSERT INTO creds VALUES(NULL, ?, ?, ?)''',
                           (b64encode(name),
                            b64encode(key),
                            b64encode(secret))
                           )
        else:
            DB_CUR.execute('''INSERT INTO creds VALUES(NULL, NULL, ?, ?)''',
                           (b64encode(key),
                            b64encode(secret))
                           )
        DB_CUR.commit()
        return 0
    except sqlite3.OperationalError:
        return -1


# gets the newest account added to the db
def getNewestAccount():
    return DB_CUR.execute('''SELECT screen_name FROM creds WHERE id = (
        SELECT max(id) FROM creds)''').fetchall()[0][0]


# gets all the screen names in the database
def getScreenNames():
    rows = DB_CUR.execute('SELECT screen_name FROM creds').fetchall()
    names = list()
    for row in rows:
        names.append(b64decode(row[0]))
    return names


# gets the id of the user in the db
def getUserId(name):
    return DB_CUR.execute('''SELECT id FROM creds
    WHERE screen_name = '%s' ''' %
                          b64encode(name)).fetchone()[0]


# gets the number of users in the db
def getUserCount():
    return DB_CUR.execute('''SELECT max(id) FROM creds''').fetchone()[0]


# if the user was added without a screen name, add it
def addUserName(name, key, secret):
    DB_CUR.execute('''UPDATE creds SET screen_name = ?
    WHERE screen_name = NULL
    AND key = ?
    AND secret = ?''',
                   (b64encode(name),
                    b64encode(key),
                    b64encode(secret)))
    DB_CUR.commit()


# returns the user's screen name
def getUser(num):
    try:
        row = DB_CUR.execute('SELECT screen_name FROM creds WHERE id = ?',
                             (str(num))
                             ).fetchall()
        return b64decode(row[0][0])
    except sqlite3.OperationalError:
        return -1


# gets the user credentials based on the screen name
def getUserCreds(name):
    res = DB_CUR.execute('''SELECT key, secret FROM creds
    WHERE screen_name = '%s' ''' %
                         b64encode(name)
                         ).fetchone()
    res = (b64decode(res[0]), b64decode(res[1]))
    return res


if system() == "Windows":
    if not path.exists(WINDOWS_PATH):
        create = open(WINDOWS_PATH, 'w+')
        create.close()
    DB_CUR = sqlite3.connect(WINDOWS_PATH)
else:
    if not path.exists(UNIX_PATH):
        create = open(UNIX_PATH, 'w+')
        create.close()
    DB_CUR = sqlite3.connect(UNIX_PATH)

try:
    DB_CUR.execute('SELECT * FROM creds')
    global TABLE_CREATED
    TABLE_CREATED = True
except sqlite3.OperationalError:
    createTable()

if system() == "Windows":
    OLD_CREDS = '.'.join((WINDOWS_PATH.split('.db')[0], 'txt'))
else:
    OLD_CREDS = UNIX_PATH.split('.db')[0]

if path.exists(OLD_CREDS):
    with open(OLD_CREDS, 'r') as f:
        creds = f.read().split('\n')
    ins = Api(consumer_key='qJwaqOuIuvZKlxwF4izCw',
              consumer_secret='53dJ9tHJ77tAE8ywZIEU60JYPyoRU9jY2v0d58nI8',
              access_token_key=creds[0],
              access_token_secret=creds[1])
    if addUser(ins.VerifyCredentials().GetScreenName(),
               creds[0],
               creds[1]) != 0:
        print "User not added to database"
    remove(OLD_CREDS)
