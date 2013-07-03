#
#
# Copyright (c) 2013, theZacAttacks
#
#

import sqlite3
from twitter import Api
from os import path, remove
from platform import system
from base64 import b64encode, b64decode

WINDOWS_PATH = path.expanduser('~\AppData\\Roaming\\tcler.db')
UNIX_PATH = path.expanduser('~/.tcler.db')
DB_CUR = None
TABLE_CREATED = False


def createTable():
    DB_CUR.execute('''CREATE TABLE creds(id PRIMARY KEY AUTOINCREMENT,
    screen_name varchar(100),
    key varchar(150),
    secret varchar(150))''')
    DB_CUR.commit()
    TABLE_CREATED = True


def getTableStatus():
    return TABLE_CREATED


def addUser(key, secret, name=None):
    try:
        if name is not None:
            DB_CUR.execute('''INSERT INTO creds VALUES(NULL, ?, ?, ?)''',
                           (b64encode(name),
                            b64encode(key),
                            b64encode(secret)))
        else:
            DB_CUR.execute('''INSERT INTO creds VALUES(NULL, NULL, ?, ?)''',
                           (b64encode(key),
                            b64encode(secret)))
        DB_CUR.commit()
        return 0
    except sqlite3.OperationalError:
        return -1


def getScreenNames():
    rows = DB_CUR.execute('SELECT screen_name FROM creds').fetchall()
    names = list()
    for row in rows:
        names.append(b64decode(row[0]))
    return names


def getUserId(key, secret):
    return DB_CUR.execute('''SELECT id FROM creds
    WHERE key = ?
    AND secret = ?''',
                          b64encode(key), b64encode(secret)).fetchall()[0][0]


def addUserName(name, key, secret):
    DB_CUR.execute('''UPDATE creds SET screen_name = ?
    WHERE screen_name = NULL
    AND key = ?
    AND secret = ?''',
                   (b64encode(name),
                    b64encode(key),
                    b64encode(secret)))
    DB_CUR.commit()


def getUser(num):
    row = DB_CUR.execute('SELECT screen_name FROM creds WHERE id = %s'
                         % num).fetchall()[0]
    return b64decode(row[0])


def getUserCreds(name):
    res = DB_CUR.execute('SELECT key, secret FROM creds WHERE screen_name = %s'
                         % b64encode(name)).fetchall()[0]
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
except sqlite3.OperationalError:
    createTable()

if system() == "Windows":
    OLD_CREDS = '.'.join((WINDOWS_PATH.split('.db')[0], 'txt'))
else:
    OLD_CREDS = '.'.join((UNIX_PATH.split('.db')[0], 'txt'))

if path.exists(OLD_CREDS):
    f = open(OLD_CREDS, 'r')
    creds = f.read().split('\n')
    f.close()
    ins = Api(consumer_key='qJwaqOuIuvZKlxwF4izCw',
              consumer_secret='53dJ9tHJ77tAE8ywZIEU60JYPyoRU9jY2v0d58nI8',
              access_token_key=creds[0],
              access_token_secret=creds[1])
    if addUser(ins.VerifyUser().screen_name,
               creds[0],
               creds[1]) != 0:
        print "User not added to database"
    remove(OLD_CREDS)
