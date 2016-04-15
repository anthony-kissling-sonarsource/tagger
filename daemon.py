#/bin/python
# -*- coding: utf-8 -*-
import logging
import socket
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
import sqlite3
from datetime import datetime
import getpass

HOST = 'localhost'        # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port

logger = logging.getLogger(__name__)    # Création du logger
logger.setLevel(logging.DEBUG)
logger.propagate = False

event_handler = FileSystemEventHandler()
observer = Observer()   # Import platform specific observer
directories = {}

# removetagDir
# Usage : Supprime récursivement le tag passé en paramètre de tous les fichiers du dossier
# Paramètre :
# - tag : Tag à supprimer
# - directory : Dossier cible
# - cursor : Curseur sur la base de données
# Retourne : rien
def removetagDir(tag, directory, cursor):
    for f in os.listdir(directory):     # Parcours de la liste des fichiers/dossiers du répértoire
        if os.path.isdir(f):
            removetagDir(os.path.realpath(directory + '/' + f))     # Appel récursif
        else:
            delTagFromFile(os.path.realpath(directory + '/' + f), tag, cursor)        # Suppression du tag
            logger.debug('tag removed')
    if not checkDirectory(directory, cursor):       # Si le dossier ne contient plus de fichiers taggés
        observer.unschedule(directories[directory]) # On arrête de le suivre
        del directories[directory]                  # Et on "l'oublie"

# tagDir
# Usage : Ajoute récursivement le tag passé en paramètre à tous les fichiers du dossier
# Paramètre :
# - tag : Tag à ajouter
# - directory : Dossier cible
# - cursor : Curseur sur la base de données
# Retourne : rien
def tagDir(tag, directory, cursor):
    for f in os.listdir(directory):
        if os.path.isdir(f):
            tagDir(os.path.realpath(directory + '/' + f))
        else:
            logger.debug(f)
            tagToFile(os.path.realpath(directory + '/' + f), tag, cursor)             # Ajout du tag
            logger.debug('tag added')
    if not followDirectory(directory, cursor):       # Si le dossier ne contient plus de fichiers
        directories[directory] = observer.schedule(event_handler, directory, recursive=False)

# connectDB
# Usage : Crée une connexion à la base de données en fonction de la platforme
# Paramètre : rien
# Retourne : L'object de connexion à la base
def connectDB():
    if sys.platform == 'linux' or sys.platform == 'linux2':
        if os.path.exists('/tmp/proj/tags.db'):     # Vérifie que la base existe
            return sqlite3.connect('/tmp/proj/tags.db', check_same_thread=False)     # Connexion à la base
        else:
            print "Lancer le script d'installation"
            exit()
    elif sys.platform == 'win32' or sys.platform == 'cygwin':
        if os.path.exists('C:\\Users\\' + getpass.getuser() + '\\tags.db'):     # Vérifie que la base existe
            return sqlite3.connect('C:\\Users\\' + getpass.getuser() + '\\tags.db', check_same_thread=False)     # Connexion à la base
        else:
            print "Lancer le script d'installation"
            exit()
    elif sys.platform == 'darwin':
        exit()
    else:
        print 'Ce système n\'est pas supporté'
        exit()

# getOrInsertFile
# Usage : Vérifie si un fichier est dans la base, l'insert sinon
# Paramètre :
# - path : Chemin du fichier
# - cursor : Curseur sur la base de données
# Retourne : id du fichier
def getOrInsertFile(path, cursor):
    # insérer le lien avec le fichier dans la base
    cursor.execute("SELECT id FROM t_file WHERE path = ? and name =?", (os.path.dirname(path), os.path.basename(path)))     # Récupère l'id du fichier dans la base (si existe)
    result = cursor.fetchall()
    if len(result) == 0:
        logger.debug('Insertion fichier')
        # Si fichier n'existe pas
        cursor.execute("INSERT INTO t_file(path, name) VALUES(?, ?)", (os.path.dirname(path), os.path.basename(path)))
        cursor.execute("SELECT id FROM t_file WHERE path = ? and name =?", (os.path.dirname(path), os.path.basename(path)))     # Récupère l'id du fichier dans la base
        result = cursor.fetchall()
    return result[0][0]

# followDirectory
# Usage : Vérifie sur un dossier est dans la base, sinon l'insert
# Paramètre :
# - directory : Chemin du dossier
# - cursor : Curseur sur la base
# Retourne : True si le dossier était déjà suivi, sinon false
def followDirectory(directory, cursor):
    # vérifier que le fichier est dans un dossier surveillé
    cursor.execute("SELECT * from t_directory where path = ?", (directory,))
    result = cursor.fetchall()
    # Si non, ajouter le dossier à la base et le suivre
    if len(result) == 0:
        cursor.execute("INSERT INTO t_directory(path) VALUES(?)", (directory,))
        logger.debug('directory followed')
        return False
    return True

# getOrInsertTag
# Usage : Vérifie si un tag est dans la base, l'insert sinon
# Paramètre :
# - tag : Tag à insérer
# - cursor : Curseur sur la base de données
# Retourne : id du tag
def getOrInsertTag(tag, cursor):
    cursor.execute('SELECT id FROM t_tag WHERE name = ?', (tag,)) # récup id du tag
    result = cursor.fetchall()
    if len(result) == 0:
        logger.debug('Insertion tag')
        cursor.execute('INSERT INTO t_tag(name, create_date) VALUES(?, CURRENT_TIMESTAMP)', (tag,))
        cursor.execute('SELECT id FROM t_tag WHERE name = ?', (tag,)) # récup id du tag
        result = cursor.fetchall()
    return result[0][0]

# delTag
# Usage : Supprime un tag de la base de données et tous les liens de celui-ci
# Paramètre :
# - tag : Tag à supprimer
# - cursor : Curseur sur la base de données
# Retourne : rien
def delTag(tag, cursor):
    cursor.execute("SELECT id FROM t_tag WHERE NAME = ?", (tag,))
    result = cursor.fetchall()
    if len(result) > 0:
        cursor.execute('DELETE FROM t_tag WHERE name = ?', (tag,))
        cursor.execute("DELETE FROM t_tag_to_file WHERE idtag = " + str(result[0][0]))

# delTagFromFile
# Usage : Supprime le lien entre un tag et un fichier
# Paramètre :
# - myfile : Fichier cible
# - tag : Tag à supprimer
# - cursor : Curseur sur la base de données
# Retourne : rien
def delTagFromFile(myfile, tag, cursor):
    cursor.execute("SELECT idtag, idfile from t_tag_to_file tf JOIN t_tag t ON (tf.idtag = t.id) JOIN t_file f ON (f.id = idfile) WHERE f.name=? and t.name=?", (os.path.basename(myfile), tag))
    result = cursor.fetchall()
    if len(result) > 0:
        cursor.execute("DELETE FROM t_tag_to_file WHERE idtag = ? and idfile = ?", result[0])

# tagToFile
# Usage : Ajoute un lien entre un tag et un fichier
# Paramètre :
# - myfile : Fichier cible
# - tag : Tag à ajouter
# - cursor : Curseur sur la base de données
# Retourne : rien
def tagToFile(myfile, tag, cursor):
    idtag = getOrInsertTag(tag, cursor)
    idfile = getOrInsertFile(myfile, cursor)
    cursor.execute("SELECT * FROM t_tag_to_file WHERE idtag = ? and idfile = ?", (idtag, idfile))
    result = cursor.fetchall()
    if len(result) == 0:
        cursor.execute("INSERT INTO t_tag_to_file(idfile, idtag, create_date) VALUES(?, ?, CURRENT_TIMESTAMP)", (idfile, idtag))

# checkTags
# Usage : Vérifie s'il y a des tags inutilisés dans la base et, si oui, les supprime
# Paramètre :
# - cursor : Curseur sur la base de données
# Retourne : rien
def checkTags(cursor):
    cursor.execute("DELETE FROM t_tag WHERE id not in (SELECT idtag FROM t_tag_to_file)")

# checkFiles
# Usage : Vérifie s'il y a des fichiers inutilisés dans la base et, si oui, les supprime
# Paramètre :
# - cursor : Curseur sur la base de données
# Retourne : rien
def checkFiles(cursor):
    cursor.execute("DELETE FROM t_file WHERE id not in (SELECT idfile FROM t_tag_to_file)")

# checkDirectories
# Usage : Vérifie s'il y a des dossiers inutilisés dans la base et, si oui, les supprime
# Paramètre :
# - cursor : Curseur sur la base de données
# Retourne : rien
def checkDirectories(cursor):
    cursor.execute("SELECT path FROM t_directory WHERE path NOT IN (SELECT path FROM t_file)")
    for directory in cursor.fetchall():
        cursor.execute("DELETE FROM t_directory WHERE path = ?", directory)

# checkDirectory
# Usage : Vérifie si le dossier est inutilisé et, si oui, le supprime
# Paramètre :
# - directory : Dossier cible
# - cursor : Curseur sur la base de données
# Retourne : rien
def checkDirectory(directory, cursor):
    cursor.execute("SELECT path FROM t_directory WHERE path = ?", (directory,))
    result = cursor.fetchall()
    if len(result) > 0:
        return True
    else:
        return False

# searchFileWithTag
# Usage : Recherche tous les fichiers en lien avec les tags donnés
# Paramètre :
# - tags : String contenant les tags à rechercher dans la base (déjà mis en forme pour du SQL)
# - cursor : Curseur sur la base de données
# Retourne : Liste des fichiers trouvés
def searchFileWithTag(tags, cursor):
    cursor.execute("SELECT path, name from t_file WHERE %s" % (tags,))
    result = cursor.fetchall()
    if len(result) > 0:
        return result
    return []

# update_database
# Usage : Fonction de callback du watchdog
# Paramètre :
# - event : Objet représentant l'événement qui a déclenché le callback
# Retourne : rien
def update_database(event):
    conn = connectDB()
    cursor = conn.cursor()      # Récupère le curseur
    if event.event_type == 'moved':
        logger.debug('[' + datetime.today().strftime('%d-%m-%Y %H:%M:%S') + '] ' + str(event.src_path) + " " + str(event.event_type))
        if not os.path.isdir(event.src_path):
            # Séparer path et filename
            srcfilename = os.path.basename(event.src_path)
            srcfilepath = os.path.dirname(event.src_path)
            destfilename = os.path.basename(event.dest_path)
            destfilepath = os.path.dirname(event.dest_path)
            cursor.execute("UPDATE t_file SET name=?, path=? WHERE name = ? and path = ?", (destfilename, destfilepath, srcfilename, srcfilepath))
            logger.debug('Fichier mis à jour')
        else:
            cursor.execute("UPDATE t_file SET path=REPLACE(path,?,?) WHERE path = ?", (event.src_path, event.dest_path, event.src_path))   # Remplacement de la partie qui a changé dans le chemin
            cursor.execute("UPDATE t_directory SET path=REPLACE(path,?,?) WHERE path = ?", (event.src_path, event.dest_path, event.src_path))
    if event.event_type == 'created':
        if not os.path.isdir(event.src_path):
            # Ajouter tags automatique
            tagToFile(event.src_path, datetime.today().strftime('%d-%m-%Y'), cursor)     # Ajout du tag
            tagToFile(event.src_path, os.path.splitext(event.src_path)[1], cursor)     # Ajout du tag
        logger.debug('[' + datetime.today().strftime('%d-%m-%Y %H:%M:%S') + '] ' + str(event.src_path) + " " + str(event.event_type))
    if event.event_type == 'deleted':
        logger.debug('[' + datetime.today().strftime('%d-%m-%Y %H:%M:%S') + '] ' + str(event.src_path) + " " + str(event.event_type))
        if not os.path.isdir(event.src_path):
            # Séparer path et filename
            filename = os.path.basename(event.src_path)
            filepath = os.path.dirname(event.src_path)
            # Verifier si le fichier est dans la base
            cursor.execute("SELECT id FROM t_file WHERE path = ? and name = ?", (filepath,filename))
            res = cursor.fetchall()
            if len(res) > 0:
                cursor.execute("DELETE FROM t_tag_to_file WHERE idfile = ?", res[0])
                cursor.execute("DELETE FROM t_file WHERE id = ?", res[0])
                checkTags(cursor)
                checkDirectories(cursor)
        else:
            observer.unschedule(files[event.src_path])
            cursor.execute("SELECT id FROM t_file WHERE path LIKE ?", (event.src_path,))
            for f in cursor.fetchall():
                cursor.execute("DELETE FROM t_tag_to_file WHERE idfile = ?", f)
            checkTags(cursor)
            checkFiles(cursor)
            cursor.execute("DELETE FROM t_directory WHERE path = ?", (event.src_path,))
        logger.debug("[%s] Traitement terminé " % datetime.today().strftime('%d-%m-%Y %H:%M:%S'))

    conn.commit();
    conn.close()

def main():
    conn = connectDB()
    cursor = conn.cursor()      # Récupère le curseur
    logger.debug('DB connected')

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(1)
    except socket.error:
        logger.debug('Failed to create socket')
        sys.exit()

    logger.debug('Socket listening on ' + str(PORT))

    cursor.execute('SELECT DISTINCT path FROM t_directory')  # Récupère tous les dossiers suivis
    event_handler.on_moved = update_database
    event_handler.on_created = update_database
    event_handler.on_deleted = update_database
    for directory in cursor.fetchall():
        directories[directory[0]] = observer.schedule(event_handler, directory[0], recursive=False)
    conn.close()
    observer.start()

    while True:
        data = ''
        logger.debug("Waiting for connexions")
        socket_conn, addr = s.accept()
        conn = connectDB()
        cursor = conn.cursor()
        logger.debug('[%s] Request received' % datetime.today().strftime('%d-%m-%Y %H:%M:%S'))
        datasize = socket_conn.recv(6)
        data = socket_conn.recv(int(datasize))
        query = data.split('-')
        if query[0] == 'removetag':
            args = query[1].split('%')              # Récupération des arguments
            for f in args[1:]:
                if not os.path.isdir(f):
                    delTagFromFile(f, args[0], cursor)        # Suppression du tag
                    logger.debug('tag removed')
                    directory = os.path.dirname(f)    # Récupération du dossier
                    if not checkDirectory(directory, cursor):       # Si le dossier ne contient plus de fichiers
                        observer.unschedule(directories[directory]) # On arrête de le suivre
                        del directories[directory]                  # Et on "l'oublie"
                else:                    # Tag de répertoire récursif
                    removetagDir(args[0], f, cursor)
            conn.commit()
            checkTags(cursor)
            checkFiles(cursor)
            conn.commit()
        elif query[0] == 'addtag':
            args = query[1].split('%')              # Récupération des arguments
            for f in args[1:]:
                if not os.path.isdir(f):
                    tagToFile(f, args[0], cursor)             # Ajout du tag
                    logger.debug('tag added')
                    directory = os.path.dirname(f)    # Récupération du dossier
                    if not followDirectory(directory, cursor):       # Si le dossier ne contient plus de fichiers
                        directories[directory] = observer.schedule(event_handler, directory, recursive=False)
                else:                    # Tag de répertoire récursif
                    logger.debug('tagging directory')
                    tagDir(args[0], f, cursor)
            conn.commit()
        elif query[0] == 'search':
            result = []
            for r in searchFileWithTag(query[1], cursor):
                result.append(r[1] + ' - ' + r[0])
            send = socket_conn.send('%'.join(result))

        conn.close()
        socket_conn.close()
        logger.debug("[%s] Commande executée " % datetime.today().strftime('%d-%m-%Y %H:%M:%S'))

    logger.debug("Fail")
    observer.join()

if sys.platform == 'linux' or sys.platform == 'linux2':
    from daemonize import Daemonize
    fh = logging.FileHandler("/tmp/test.log", "w")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    pid = "/tmp/test.pid"
    f = open(pid, 'a')
    f.write('')
    f.close()     # Création du fichier
    keep_fds = [fh.stream.fileno()]
    daemon = Daemonize(app="proj", pid=pid, action=main, keep_fds=keep_fds)
    daemon.start()
elif sys.platform == 'darwin':
    exit()
else:
    fh = logging.FileHandler('C:\\Users\\' + getpass.getuser() + '\\daemon.log', 'a')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    main()
