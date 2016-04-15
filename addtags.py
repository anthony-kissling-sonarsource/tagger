#/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import time
import logging
import sqlite3
import socket

HOST = 'localhost'        # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port

if sys.platform == 'linux' or sys.platform == 'linux2':
    delimiter = '/'
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    delimiter = '\\'
elif sys.platform == 'darwin':
    delimiter = '/'
else:
    print 'Ce système n\'est pas supporté'
    exit()

def printHelp():
    print 'Syntax : addtags tag files [files] [files] ...'
    print 'tag : Tag à appliquer'
    print 'files : fichiers sur lesquels on applique le tag'

path = os.getcwd()        # Récupère l'utilisateur

if len(sys.argv) > 2:
    tag = sys.argv[1]
    files = []
    for i in range(2, len(sys.argv)):
        if os.path.exists(os.path.realpath(path + delimiter + str(sys.argv[i]))):
            files.append(os.path.realpath(path + delimiter + str(sys.argv[i])))
        else:
            files.append(os.path.realpath(str(sys.argv[i])))
else:
    printHelp();
    sys.exit()     # récupère le mode (premier argument)

#if socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((HOST, PORT)) != 0:
#    print 'Daemon introuvable'
#    sys.exit();

msg = 'addtag-' + tag
for n in files:
    msg = msg + '%' + n

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send('%06d' % len(msg))   # Envoi la taille des données qui vont être envoyée par la suite
print len(msg)
s.send(msg)
s.close()
