from charms.reactive import when, when_all, when_not, set_state, hook
from charmhelpers.fetch import apt_install, add_source, apt_update
from charmhelpers.core import host
from charmhelpers.core import hookenv
from pathlib import Path
from zipfile import ZipFile
from libsonarr import SonarrHelper

import os
import shutil
import time
import socket

sh = SonarrHelper()


@hook('upgrade-charm')
def handle_upgrade():
    if not sh.kv.get('mono-source'):
        add_source("deb https://download.mono-project.com/repo/ubuntu stable-{series} main", key="3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF")
        apt_update()
        apt_install(sh.deps)
        host.service_restart(sh.service_name)
        sh.kv.set('mono-source', 'mono-project')


@when('layer-service-account.configured')
@when_not('sonarr.installed')
def install_sonarr():
    hookenv.status_set('maintenance', 'installing sonarr')
    # Mono
    add_source("deb https://download.mono-project.com/repo/ubuntu stable-{series} main", key="3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF")
    sh.kv.set('mono-source', 'mono-project')
    # Sonarr
    add_source("deb http://apt.sonarr.tv/ master main", key='''
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
    dependencies = sh.deps
    dependencies.append('nzbdrone')
    apt_install(dependencies)
    os.chmod('/opt/', 0o777)
    shutil.chown('/opt/NzbDrone', user=sh.user, group=sh.user)
    host.chownr('/opt/NzbDrone', owner=sh.user, group=sh.user)
    host.mkdir(sh.home_dir, owner=sh.user, group=sh.user, perms=0o750)
    hookenv.status_set('maintenance', 'installed')
    set_state('sonarr.installed')


@when('sonarr.installed')
@when_not('sonarr.autostart')
def auto_start():
    hookenv.status_set('maintenance', 'setting up auto-start')
    sh.setup_systemd()
    set_state('sonarr.autostart')


@when_all('sonarr.autostart', 'layer-hostname.installed')
@when_not('sonarr.configured')
def setup_config():
    hookenv.status_set('maintenance', 'configuring sonarr')
    backups = './backups'
    if sh.charm_config['restore-config']:
        try:
            os.mkdir(backups)
        except OSError as e:
            if e.errno is 17:
                pass
        backupFile = hookenv.resource_get('sonarrconfig')
        if backupFile:
            with ZipFile(backupFile, 'r') as inFile:
                inFile.extractall(sh.config_dir)
            hookenv.log("Restoring config, indexers are disabled enable with action when configuration has been checked", 'INFO')
            # Turn off indexers
            sh.set_indexers(False)
        else:
            hookenv.log("Add sonarrconfig resource, see juju attach or disable restore-config", 'WARN')
            hookenv.status_set('blocked', 'waiting for sonarrconfig resource')
            return
    else:
        host.service_start(sh.service_name)
        configFile = Path(sh.config_file)
        while not configFile.is_file():
            hookenv.log("Waiting for service to start", 'INFO')
            time.sleep(5)
    sh.modify_config(port=sh.charm_config['port'], urlbase='None')
    hookenv.open_port(sh.charm_config['port'], 'TCP')
    host.service_start(sh.service_name)
    hookenv.status_set('active', 'Sonarr is ready')
    set_state('sonarr.configured')


@when_not('usenet-downloader.configured')
@when_all('usenet-downloader.triggered', 'usenet-downloader.available', 'sonarr.configured')
def configure_downloader(usenetdownloader, *args):
    hookenv.log("Setting up sabnzbd relation requires editing the database and may not work", "WARNING")
    sh.setup_sabnzbd(port=usenetdownloader.port(),
                     apikey=usenetdownloader.apikey(),
                     hostname=usenetdownloader.hostname())
    usenetdownloader.configured()


@when_not('plex-info.configured')
@when_all('plex-info.triggered', 'plex-info.available', 'sonarr.configured')
def configure_plex(plexinfo, *args):
    hookenv.log("Setting up plex relation requires editing the database and may not work", "WARNING")
    sh.setup_plex(hostname=plexinfo.hostname(), port=plexinfo.port(),
                  user=plexinfo.user(), passwd=plexinfo.passwd())
    plexinfo.configured()


@when_all('reverseproxy.triggered', 'reverseproxy.ready')
@when_not('reverseproxy.configured', 'reverseproxy.departed')
def configure_reverseproxy(reverseproxy, *args):
    hookenv.log("Setting up reverseproxy", "INFO")
    proxy_info = {'urlbase': sh.charm_config['proxy-url'],
                  'subdomain': sh.charm_config['proxy-domain'],
                  'group_id': sh.charm_config['proxy-group'],
                  'external_port': sh.charm_config['proxy-port'],
                  'internal_host': socket.getfqdn(),
                  'internal_port': sh.charm_config['port']
                  }
    reverseproxy.configure(proxy_info)
    sh.modify_config(urlbase=sh.charm_config['proxy-url'])
    host.service_restart(sh.service_name)


@when_all('reverseproxy.triggered', 'reverseproxy.departed')
def remove_urlbase(reverseproxy, *args):
    hookenv.log("Removing reverseproxy configuration", "INFO")
    sh.modify_config(urlbase='None')
    host.service_restart(sh.service_name)


