from subprocess import Popen
import subprocess

pid = Popen(["C:\python27\python.exe", "daemon.py"], creationflags=8, close_fds=True).pid
print pid
print 'done'