#!/usr/bin/python3
#from charmhelpers.core.hookenv import log
from charmhelpers.core import hookenv
from charmhelpers.core import host #adduser, service_start, service_stop, service_restart, chownr
import fileinput
import shutil
import sqlite3
import json

def HelloWorld():
    hookenv.log("Hello World!","INFO")

def modify_config(port=None,sslport=None,auth=None,urlbase=None):
    '''
    Modify the config.xml file for sonarr, this will cause a sonarr restart
    port: The value to use for the port, if not specified will leave unmodified
    sslport: The value to use for the sslport, if not specified will leave unmodified
    auth: The value to use for Authentication, if not specified will leave unmodified
          Setting auth to 'None' will disable authenticaiton and is the only value tested for modifying the config
    urlbase: The value to use for the urlbase, if not specified will leave unmodified
             Default urlbase is an empty string, passing a string of 'None' will set an empty string
    '''
    config = hookenv.config()
    configFile = '/home/{}/.config/NzbDrone/config.xml'.format(config['sonarruser'])
    for line in fileinput.input(configFile,inplace=True):
        if line.strip().startswith('<Port>') and port:
            line = '  <Port>{}</Port>\n'.format(port)
        if line.strip().startswith('<UrlBase>') and urlbase:
            if urlbase == "None":
                line = '  <UrlBase></UrlBase>\n'
            else:
                line = '  <UrlBase>{}</UrlBase>\n'.format(urlbase)
        if line.strip().startswith('<SslPort>') and sslport:
            line = '  <SslPort>{}</SslPort>\n'.format(sslport)
        if line.strip().startswith('<AuthenticationMethod>') and auth:
            line = '  <AuthenticationMethod>{}</AuthenticationMethod>\n'.format(auth)
        print(line,end='')
    shutil.chown('/home/{}/.config/NzbDrone/config.xml'.format(config['sonarruser']),user=config['sonarruser'],group=config['sonarruser'])
    host.service_restart('sonarr.service')
    hookenv.log('sonarr config modified','INFO')

def set_indexers(status):
    '''Enable or disable all indexer searching based on provided status
    status: True will turn on indexers
    status: False will turn off indexers'''
    config = hookenv.config()
    conn = sqlite3.connect('/home/{}/.config/NzbDrone/nzbdrone.db'.format(config['sonarruser']))
    c = conn.cursor()
    if status:
        c.execute('''UPDATE Indexers SET EnableRss = 1, EnableSearch = 1''')
    else:
        c.execute('''UPDATE Indexers SET EnableRss = 0, EnableSearch = 0''')
    conn.commit()
    host.chownr('/home/{}'.format(config['sonarruser']),owner=config['sonarruser'],group=config['sonarruser'])
 
def setup_plex(hostname,port,user=None,passwd=None):
    '''' Modify an existing plex Notification or create one with the given settings
    hostname: The address for the plex server
    port: The plex port
    user: (Optional) plex user name
    passwd: (Optional) plex password'''
    config = hookenv.config()
    host.service_stop('sonarr.service')
    conn = sqlite3.connect('/home/{}/.config/NzbDrone/nzbdrone.db'.format(config['sonarruser']))
    c = conn.cursor()
    c.execute('''SELECT Settings FROM Notifications WHERE ConfigContract is "PlexServerSettings"''')
    result = c.fetchall()
    if len(result):
        hookenv.log("Modifying existing plex setting for sonarr","INFO")
        row = result[0]
        settings = json.loads(row[0])
        settings['host'] = hostname
        settings['port'] = port
        settings['username'] = settings['username'] or user
        settings['password'] = settings['password'] or passwd
        conn.execute('''UPDATE Notifications SET Settings = ? WHERE ConfigContract is "PlexServerSettings"''',(json.dumps(settings),))
    else:
        hookenv.log("Creating plex setting for sonarr.","INFO")
        settings = {"host": hostname, "port": port, "username": user or "", "password": passwd or "", "updateLibrary": True, "useSsl": False, "isValid": True}
        c.execute('''INSERT INTO Notifications (Name,OnGrab,onDownload,Settings,Implementation,ConfigContract,OnUpgrade,Tags,OnRename) VALUES (?,?,?,?,?,?,?,?,?)''',("Plex",0,1,json.dumps(settings),"PlexServer","PlexServerSettings",1,None,1))
    conn.commit()
    host.service_start('sonarr.service')
 #.schema Notifications
#CREATE TABLE "Notifications" ("Id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "Name" TEXT NOT NULL, "OnGrab" INTEGER NOT NULL, "OnDownload" INTEGER NOT NULL, "Settings" TEXT NOT NULL, "Implementation" TEXT NOT NULL, "ConfigContract" TEXT, "OnUpgrade" INTEGER, "Tags" TEXT, "OnRename" INTEGER NOT NULL);
#sqlite> SELECT * FROM Notifications;
#   1|Plex|0|1|{
#   "host": "192.168.0.10",
#   "port": 32400,
#   "username": "",
#   "password": "",
#   "updateLibrary": true,
#   "useSsl": false,
#   "isValid": true
#   }|PlexServer|PlexServerSettings|1|[]|1


