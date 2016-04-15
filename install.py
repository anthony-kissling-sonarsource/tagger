#/bin/python
# -*- coding: utf-8 -*-
import socket
import sys
import os
import sqlite3
import getpass

# Fonction de création de la base de donnée
def createdb():
    cursor.execute("CREATE TABLE t_file(id INTEGER PRIMARY KEY AUTOINCREMENT, path CHAR(75), name CHAR(50))")
    cursor.execute("CREATE TABLE t_directory(id INTEGER PRIMARY KEY AUTOINCREMENT, path CHAR(75))")
    cursor.execute("CREATE TABLE t_tag(id INTEGER PRIMARY KEY AUTOINCREMENT, name CHAR(50), create_date DATETIME)")
    cursor.execute("CREATE TABLE t_tag_to_file(idfile INTEGER NOT NULL, idtag INTEGER NOT NULL, create_date DATETIME, FOREIGN KEY(idfile) REFERENCES t_file(id) ON DELETE CASCADE, FOREIGN KEY(idtag) REFERENCES t_tag(id) ON DELETE CASCADE)")
    conn.commit()

if sys.platform == 'linux' or sys.platform == 'linux2':
    if not os.path.exists('/tmp/proj/tags.db'):     # Vérifie que la base existe
        if not os.path.exists('/tmp/proj'):
            os.makedirs('/tmp/proj')
        conn = sqlite3.connect('/tmp/proj/tags.db', check_same_thread=False)
        cursor = conn.cursor()
        createdb()
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    if not os.path.exists('C:\\Users\\' + getpass.getuser() + '\\tags.db'):     # Vérifie que la base existe
        conn = sqlite3.connect('C:\\Users\\' + getpass.getuser() + '\\tags.db', check_same_thread=False)
        cursor = conn.cursor()
        createdb()
elif sys.platform == 'darwin':
    exit()
else:
    print 'Ce système n\'est pas supporté'
    exit()
