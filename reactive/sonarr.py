from charms.reactive import when, when_all, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.fetch import apt_install, add_source, apt_update
from charmhelpers.core.host import adduser, service_start, service_restart, chownr
from charmhelpers.core.hookenv import status_set, log, resource_get
import os
import random
import string
import fileinput
import socket
import tarfile

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
    adduser(config['sonarruser'],password=''''''.join([random.choice(string.printable) for _ in range(random.randint(8, 12))]),home_dir='/home/'+config['sonarruser'])
    apt_install('nzbdrone')
    status_set('active','')
    set_state('sonarr.installed')
    hookenv.open_port(config['port'],'TCP')

@when('sonarr.installed')
@when_not('sonarr.autostart')
def auto_start():
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
TimeoutStopSec=20
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
'''.format(user=config['sonarruser'],\
           group=config['sonarruser'],\
           mono='/usr/bin/mono',\
           sonarr='/opt/NzbDrone/NzbDrone.exe'))
    service_start('sonarr.service')
    set_state('sonarr.autostart')

#@when_all('sonarr.installed','layer-hostname.installed')
#@when_not('sonarr.restored')
#def restore_user_conf():
#    config = hookenv.config()
#    backups = './backups'
#    if config['restore-config']:
#        try:
#            os.mkdir(backups)
#        except OSError as e:
#            if e.errno is 17:
#              pass
#        backupFile = resource_get('sabconfig')
#        if backupFile:
#            with tarfile.open(backupFile,'r:gz') as inFile:
#                inFile.extractall('/home/{}'.format(config['sabuser']))
#            for line in fileinput.input('/home/{}/.sonarr/sonarr.ini'.format(config['sabuser']), inplace=True):
#                if line.startswith("host="):
#                    line = "host={}\n".format(socket.gethostname())
#                print(line,end='') # end statement to avoid inserting new lines at the end of the line
#            log("Changing configuration for new host but not ports. The backup configuration will override charm port settings!",'WARNING')
#            chownr('/home/{}/.sonarr'.format(config['sabuser']),owner=config['sabuser'],group=config['sabuser'])
#        else:
#            log("Add sabconfig resource, see juju attach or disable restore-config",'ERROR')
#            raise ValueError('Sabconfig resource missing, see juju attach or disable restore-config')
#    set_state('sonarr.restored')
        

#@when_all('sonarr.restored')
#@when_not('sonarr.configured')
#def write_configs():
#    config = hookenv.config()
#    status_set('maintenance','configuring sonarr')
#    address = socket.gethostname()
#    for line in fileinput.input('/etc/default/sonarrplus', inplace=True):
#        if line.startswith("USER="):
#            line = "USER={}\n".format(config['sabuser'])
#        if line.startswith("HOST="):
#            line = "HOST={}\n".format(address)
#        if line.startswith("PORT=\n"):
#            line = "PORT={}".format(config['port'])
#        print(line,end='') # end statement to avoid inserting new lines at the end of the line
#    hookenv.open_port(config['port'],'TCP')
#    service_restart('sonarrplus')
#    status_set('active','')
#    set_state('sonarr.configured')
#    set_state('sonarr.ready')

# TODO add relations
