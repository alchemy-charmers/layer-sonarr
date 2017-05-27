#!/usr/bin/python3
#from charmhelpers.core.hookenv import log
from charmhelpers.core import hookenv
from charmhelpers.core import host #adduser, service_start, service_stop, service_restart, chownr
import fileinput
import shutil

def HelloWorld():
    hookenv.log("Hello World!","INFO")

def modify_config(port=None,sslport=None,auth=None):
    config = hookenv.config()
    configFile = '/home/{}/.config/NzbDrone/config.xml'.format(config['sonarruser'])
    for line in fileinput.input(configFile,inplace=True):
        if line.strip().startswith('<Port>') and port:
            line = '  <Port>{}</Port>\n'.format(port)
        if line.strip().startswith('<SslPort>') and sslport:
            line = '  <SslPort>{}</SslPort>\n'.format(sslport)
        if line.strip().startswith('<AuthenticationMethod>') and auth:
            line = '  <AuthenticationMethod>{}</AuthenticationMethod>\n'.format(auth)
        print(line,end='')
    shutil.chown('/home/{}/.config/NzbDrone/config.xml'.format(config['sonarruser']),user=config['sonarruser'],group=config['sonarruser'])
    host.service_restart('sonarr.service')
    hookenv.log('Authentication disabled','INFO')
