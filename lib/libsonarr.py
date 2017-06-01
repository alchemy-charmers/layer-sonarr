#!/usr/bin/python3
#from charmhelpers.core.hookenv import log
from charmhelpers.core import hookenv
from charmhelpers.core import host #adduser, service_start, service_stop, service_restart, chownr
import fileinput
import shutil
import sqlite3

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
    hookenv.log('Authentication disabled','INFO')

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
 
