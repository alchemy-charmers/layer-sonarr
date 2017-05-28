from charms.reactive import when, when_all, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.fetch import apt_install, add_source, apt_update
from charmhelpers.core.host import adduser, service_start, service_stop, service_restart, chownr
from charmhelpers.core.hookenv import status_set, log, resource_get
from pathlib import Path
from zipfile import ZipFile

import libsonarr
import os
import subprocess
import random
import string
import fileinput
import socket
import tarfile
import shutil
import time
import sqlite3
import json

@when_not('sonarr.installed')
def install_sonarr():
    config = hookenv.config()
    status_set('maintenance','installing sonarr')
    add_source("deb http://apt.sonarr.tv/ master main",key='''
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQENBFIdLCUBCADL27NXM4ZdnIL9e+2wYlHAT8PNEVVsJzS6xYaNaRF6Z9w1qz9N
qtxI3snY2O3SvaIu6+yRbrTtxghATMjvV/n/kglfffgT04OvzIu7mdN7vYlQ+X3I
3hWZtpJc4pq1RGBErNJ4WSyxqb646EVjrmNRuMMdIG3Pwy8L+5V2f9H/5u2eD8X5
yJvjZgZwjDBIaeLbu/NP2M6GnvDz1UgGY9irCRSuV7/QlxutEQQFcaxpdbTjlnEZ
+/CW/Td8+lAZ3LERyQrihUshV02IZw9/uj4PdjUyZBt/cTXUoMkxopDFrZxZ1+6Z
nzp5WQdcUqyJlmQ3/WTpy9FwExfbicMeHa+FABEBAAG0H056YkRyb25lIDxjb250
YWN0QG56YmRyb25lLmNvbT6JATgEEwECACIFAlIdLCUCGwMGCwkIBwMCBhUIAgkK
CwQWAgMBAh4BAheAAAoJEOv/a5nZt4STC6QH/j3GjVaDK/Y47pmg50PgDHohZfMo
HlMCENxfFwL8sEu63t1E29A+4qgLS1RTRxewc8YrXDYzFhkR9yd71Y/+ydwSRXNF
43hM/KBxh3ssbTuS6EsLKOhfZtjWsMbHJwNhdDtyKyYe5A//5EGl0Tj+EMUV04HY
3Z0INPYBe6igmfSrjaDK3yat/Bl3HR4lQwd7au4DLp488BE70XSlx240/Z1LQErw
qvcPQ95fBZsWot2jOiPIAOQuoDHqYSCd7ICjVHoaSLCmADej1K5rPcQ3YE3z/Okn
JZs/Hn9GmshWcOodzQOmgsmzkPn3yunjamWoPHvsaAMCcE2pVC/ZiYkyJAa5AQ0E
Uh0sJQEIAMiL7P0xLpdOQejcDD7igAvvWFIDHK487M/RP1o8BrQ7tBOLnDqKH1Lt
VffqrCS6MA2sQxYUv4Fx+HYH90BCqbkP0fRWVkREVONDb9ZgfyA4a9rpcZeM9oJX
qBChQjMrK6yM0yvbiIbKgxGs6ZpnxeAk5Ebgwkgrc8G44EPDM1w8lZA3tN8VQXMq
P/Vx8eLCpIviK8iEAos/tq14FGZUFTpPstFrgo1Zj6tc3zQqXHpAd3t9dQrtZNEA
NxnI+Dn/BMsUVmsMi/RS2y5Dg7iCPzXXrZUAQfLgUa3ofHvbTYwU4KecgRMege4n
zD9IjiVPCdpFMQCPPkajKhqzbmcoQ0sAEQEAAYkBHwQYAQIACQUCUh0sJQIbDAAK
CRDr/2uZ2beEk2/iB/4i4jp6aNEBiRZ+oxobTGeAlS8ttK+knlZifMPGC43iAL9i
MNOxV5D4eLAs1IRDYypB+qkjqZPiuTVlQCDBlEDQtZoUNCYUDZqSHPL7OzkeKFc2
h+o90rp2yDzhe3rVBuvEQp69n6qfVlNeWhQjPsxiLMQALlGRJWvdGl1cr6nevQ6s
Vm+pgH7rfgOPYRFlWmw/rQo6FcZjKPuBBjyjhC394WOHPW7v9HUn98UQzyD3A/sc
Qd/aWLSP9oZyapJsMlRHfLCptwoXMCFoH4TJS6PiEJ2DI9KRDEXuk9ueKKhbM11z
gX27DCbagJxljizL7n8mzeGG4qopDEU0jQ0sAXVh
=S/mr
-----END PGP PUBLIC KEY BLOCK-----

''')
    apt_update()
    adduser(config['sonarruser'],password=r''''''.join([random.choice(string.printable) for _ in range(random.randint(8, 12))]),home_dir='/home/'+config['sonarruser'])
    apt_install('nzbdrone')
    os.chmod('/opt/',0o777)
    shutil.chown('/opt/NzbDrone',user=config['sonarruser'],group=config['sonarruser'])
    chownr('/opt/NzbDrone',owner=config['sonarruser'],group=config['sonarruser'])
    status_set('maintenance','installed')
    set_state('sonarr.installed')

@when('sonarr.installed')
@when_not('sonarr.autostart')
def auto_start():
    status_set('maintenance','setting up auto-start')
    with open('/lib/systemd/system/sonarr.service','w') as serviceFile:
        config = hookenv.config()
        serviceFile.write('''
[Unit]
Description=Sonarr Daemon
After=syslog.target network.target

[Service]
User={user}
Group={group}

Type=simple
ExecStart={mono} --debug {sonarr} -nobrowser
ExecStopPost=/usr/bin/killall -9 mono
TimeoutStopSec=20
KillMode=process
Restart=always

[Install]
WantedBy=multi-user.target
'''.format(user=config['sonarruser'],\
           group=config['sonarruser'],\
           mono='/usr/bin/mono',\
           sonarr='/opt/NzbDrone/NzbDrone.exe'))
    subprocess.check_call("systemctl enable sonarr.service",shell=True)
    set_state('sonarr.autostart')

@when_all('sonarr.autostart','layer-hostname.installed')
@when_not('sonarr.configured')
def setup_config():
    status_set('maintenance','configuring sonarr')
    config = hookenv.config()
    backups = './backups'
    if config['restore-config']:
        try:
            os.mkdir(backups)
        except OSError as e:
            if e.errno is 17:
              pass
        backupFile = resource_get('sonarrconfig')
        if backupFile:
            with ZipFile(backupFile,'r') as inFile:
            #with tarfile.open(backupFile,'r:gz') as inFile:
                inFile.extractall('/home/{}/.config/NzbDrone'.format(config['sonarruser']))
            log("Restoring config, the restored configuration will override charm port settings",'INFO')
            # Turn off indexers
            config = hookenv.config()
            conn = sqlite3.connect('/home/{}/.config/NzbDrone/nzbdrone.db'.format(config['sonarruser']))
            c = conn.cursor()
            c.execute('''UPDATE Indexers SET EnableRss = 0, EnableSearch = 0''')
            conn.commit()
            chownr('/home/{}'.format(config['sonarruser']),owner=config['sonarruser'],group=config['sonarruser'])
        else:
            log("Add sonarrconfig resource, see juju attach or disable restore-config",'WARN')
            status_set('blocked','waiting for sonarrconfig resource')
            return
    else:
        service_start('sonarr.service')
        configFile = Path('/home/{}/.config/NzbDrone/config.xml'.format(config['sonarruser']))
        while not configFile.is_file():
            time.sleep(1)
    #libsonarr.modify_config(port=config['port'],sslport=config['ssl-port'],auth='None')
    libsonarr.modify_config(port=config['port'],sslport=config['ssl-port'])
    hookenv.open_port(config['port'],'TCP')
    # TODO: How does ssl port work for sonarr, looks to require more config
    #hookenv.open_port(config['ssl-port'],'TCP')
    service_start('sonarr.service')
    status_set('active','')
    set_state('sonarr.configured')
        
@when_not('usenet-downloader.configured')
@when_all('usenet-downloader.triggered','usenet-downloader.available','sonarr.configured')
def configure_downloader(usenetdownloader,*args):
    log("Setting up sabnzbd relation requires editing the database and may not work","WARNING")
    service_stop('sonarr.service')
    config = hookenv.config()
    conn = sqlite3.connect('/home/{}/.config/NzbDrone/nzbdrone.db'.format(config['sonarruser']))
    c = conn.cursor()
    c.execute('''SELECT Settings FROM DownloadClients WHERE ConfigContract is "SabnzbdSettings"''')
    result = c.fetchall()
    if len(result):
        log("Modifying existing sabnzbd setting for sonarr.","INFO")
        row = result[0]
        settings = json.loads(row[0])
        settings['port'] = usenetdownloader.port()
        settings['apiKey'] = usenetdownloader.apikey()
        settings['host'] = usenetdownloader.hostname()
        conn.execute('''UPDATE DownloadClients SET Settings = ? WHERE ConfigContract is "SabnzbdSettings"''',(json.dumps(settings),))
    else:
        log("Creating sabnzbd setting for sonarr.","INFO")
        settings = {"tvCategory": "tv", "port": usenetdownloader.port(), "apiKey": usenetdownloader.apikey(), "olderTvPriority": -100, "host": usenetdownloader.hostname(), "useSsl": False, "recentTvPriority": -100}
        c.execute('''INSERT INTO DownloadClients (Enable,Name,Implementation,Settings,ConfigContract) VALUES (?,?,?,?,?)''',(1,'Sabnzbd','Sabnzbd',json.dumps(settings),'SabnzbdSettings'))
    conn.commit()
    service_start('sonarr.service')
    usenetdownloader.configured()
   
