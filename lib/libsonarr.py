#!/usr/bin/python3
from charmhelpers.core import hookenv
from charmhelpers.core import host  # adduser, service_start, service_stop, service_restart, chownr
from charmhelpers.core import templating
from charmhelpers.core import unitdata

import fileinput
import shutil
import sqlite3
import json
import subprocess


class SonarrHelper:
    def __init__(self):
        self.charm_config = hookenv.config()
        self.user = "sonarr"  # This is set in the service-layer configs
        self.executable = '/opt/NzbDrone/NzbDrone.exe'
        self.mono_path = '/usr/bin/mono'
        self.home_dir = '/home/{}'.format(self.user)
        self.config_dir = self.home_dir + '/.config/NzbDrone'
        self.database_file = self.config_dir + '/nzbdrone.db'
        self.config_file = self.config_dir + '/config.xml'
        self.service_name = 'sonarr.service'
        self.service_file = '/lib/systemd/system/' + self.service_name
        self.kv = unitdata.kv()
        self.deps = [
            'mono-complete',
        ]

    def modify_config(self, port=None, sslport=None, auth=None, urlbase=None):
        '''
        Modify the config.xml file for sonarr, this will cause a sonarr restart
        port: The value to use for the port, if not specifiedwill leave unmodified
        sslport: The value to use for the sslport, if not specified will leave unmodified
        auth: The value to use for Authentication, if not specified will leave unmodified
              Setting auth to 'None' will disable authenticaiton and is the only value tested for modifying the config
        urlbase: The value to use for the urlbase, if not specified will leave unmodified
                 Default urlbase is an empty string, passing a string of 'None' will set an empty string
        '''
        for line in fileinput.input(self.config_file, inplace=True):
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
            print(line, end='')
        shutil.chown(self.config_file, user=self.user, group=self.user)
        host.service_restart(self.service_name)
        hookenv.log('sonarr config modified', 'INFO')

    def set_indexers(self, status):
        '''Enable or disable all indexer searching based on provided status
        status: True will turn on indexers
        status: False will turn off indexers'''
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        if status:
            c.execute('''UPDATE Indexers SET EnableRss = 1, EnableSearch = 1''')
        else:
            c.execute('''UPDATE Indexers SET EnableRss = 0, EnableSearch = 0''')
        conn.commit()
        host.chownr(self.home_dir, owner=self.user,
                    group=self.user)

    def setup_systemd(self):
        context = {'user': self.user,
                   'group': self.user,
                   'mono': self.mono_path,
                   'sonarr': self.executable
                   }
        templating.render(source=self.service_name,
                          target=self.service_file,
                          context=context)
        subprocess.check_call("systemctl enable {}".format(self.service_name), shell=True)

    def setup_sabnzbd(self, port, apikey, hostname):
        host.service_stop(self.service_name)
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute('''SELECT Settings FROM DownloadClients WHERE ConfigContract is "SabnzbdSettings"''')
        result = c.fetchall()
        if len(result):
            hookenv.log("Modifying existing sabnzbd setting for sonarr", "INFO")
            row = result[0]
            settings = json.loads(row[0])
            settings['port'] = port
            settings['apiKey'] = apikey
            settings['host'] = hostname
            conn.execute('''UPDATE DownloadClients SET Settings = ? WHERE ConfigContract is "SabnzbdSettings"''',
                         (json.dumps(settings),))
        else:
            hookenv.log("Creating sabnzbd setting for sonarr.", "INFO")
            settings = {"tvCategory": "tv", "port": port, "apiKey": apikey,
                        "olderTvPriority": -100, "host": hostname, "useSsl": False, "recentTvPriority": -100}
            c.execute('''INSERT INTO DownloadClients
                      (Enable,Name,Implementation,Settings,ConfigContract) VALUES
                      (?,?,?,?,?)''',
                      (1, 'Sabnzbd', 'Sabnzbd', json.dumps(settings), 'SabnzbdSettings'))
        conn.commit()
        host.service_start(self.service_name)

    def setup_plex(self, hostname, port, user=None, passwd=None):
        '''' Modify an existing plex Notification or create one with the given settings
        hostname: The address for the plex server
        port: The plex port
        user: (Optional) plex user name
        passwd: (Optional) plex password'''
        host.service_stop(self.service_name)
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute('''SELECT Settings FROM Notifications WHERE ConfigContract is "PlexServerSettings"''')
        result = c.fetchall()
        if len(result):
            hookenv.log("Modifying existing plex setting for sonarr", "INFO")
            row = result[0]
            settings = json.loads(row[0])
            settings['host'] = hostname
            settings['port'] = port
            settings['username'] = settings['username'] or user
            settings['password'] = settings['password'] or passwd
            conn.execute('''UPDATE Notifications SET Settings = ? WHERE ConfigContract is "PlexServerSettings"''',
                         (json.dumps(settings),))
        else:
            hookenv.log("Creating plex setting for sonarr.", "INFO")
            settings = {"host": hostname, "port": port, "username": user or "", "password": passwd or "",
                        "updateLibrary": True, "useSsl": False, "isValid": True}
            c.execute('''INSERT INTO Notifications
                      (Name,OnGrab,onDownload,Settings,Implementation,ConfigContract,OnUpgrade,Tags,OnRename)
                      VALUES (?,?,?,?,?,?,?,?,?)''', ("Plex", 0, 1,
                                                      json.dumps(settings),
                                                      "PlexServer",
                                                      "PlexServerSettings", 1, None,
                                                      1))
        conn.commit()
        host.service_start(self.service_name)

# .schema Notifications
# CREATE TABLE "Notifications" ("Id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "Name" TEXT NOT NULL, "OnGrab" INTEGER NOT NULL,
#                               "OnDownload" INTEGER NOT NULL, "Settings" TEXT NOT NULL, "Implementation" TEXT NOT NULL,
#                               "ConfigContract" TEXT, "OnUpgrade" INTEGER, "Tags" TEXT, "OnRename" INTEGER NOT NULL);
# sqlite> SELECT * FROM Notifications;
#    1|Plex|0|1|{
#    "host": "192.168.0.10",
#    "port": 32400,
#    "username": "",
#    "password": "",
#    "updateLibrary": true,
#    "useSsl": false,
#    "isValid": true
#    }|PlexServer|PlexServerSettings|1|[]|1


