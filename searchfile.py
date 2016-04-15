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

def evaluateNPI(args):
    stack = []
    for i in args:
        if i == '@or':
            a = stack.pop()
            b = stack.pop()
            stack.append('(' + a + ' or ' + b + ')')
        elif i == '@and':
            a = stack.pop()
            b = stack.pop()
            stack.append('(' + a + ' and ' + b + ')')
        elif i == '@not':
            a = stack.pop()
            a = a.replace(' IN ',' NOT IN ')
            stack.append(a)
        else:
            stack.append('id IN (SELECT idfile FROM t_tag_to_file tf JOIN t_tag t ON (t.id = tf.idtag) WHERE t.name = \'' + i + '\')')
    return stack[0]

def printHelp():
    print 'Syntax : searchfile tag'
    print 'Syntax : searchfile --npi tag tag @not @or tag @and'
    print 'tag : Tag à chercher'
    print '--npi : Active la recherche par notation polonaise inverse'

if len(sys.argv) > 1:
    if sys.argv[1] == '--npi':
        r = evaluateNPI(sys.argv[2:])
    else:
        r = ''
        for i in range(1, len(sys.argv)):
            r += 'id IN (SELECT idfile FROM t_tag_to_file tf JOIN t_tag t ON (t.id = tf.idtag) WHERE t.name = \'' + sys.argv[i] + '\') and '
        r = r[:len(r)-5]
else:
    printHelp();
    sys.exit()     # récupère le mode (premier argument)

#if socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((HOST, PORT)) != 0:
#    print 'Daemon introuvable'
#    sys.exit();

msg = 'search-' + r

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send('%06d' % len(msg))   # Envoi la taille des données qui vont être envoyée par la suite
s.send(msg)   # Envoi la taille des données qui vont être envoyée par la suite
res = s.recv(1024)   # Attention si rien de trouvé
for f in res.split('%'):
    print f
s.close()
