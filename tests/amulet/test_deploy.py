#!/usr/bin/python3

import pytest
import amulet
import requests
import time


@pytest.fixture(scope="module")
def deploy():
    deploy = amulet.Deployment(series='xenial')
    deploy.add('sonarr')
    deploy.add('haproxy', charm='~chris.sanders/haproxy')
    deploy.expose('haproxy')
    deploy.configure('sonarr', {'backup-count': 1,
                                'backup-location': '/tmp/sonarr',
                                'proxy-port': 80})
    deploy.setup(timeout=1000)
    return deploy


@pytest.fixture(scope="module")
def haproxy(deploy):
    return deploy.sentry['haproxy'][0]


@pytest.fixture(scope="module")
def sonarr(deploy):
    return deploy.sentry['sonarr'][0]


class TestSonarr():

    def test_deploy(self, deploy):
        try:
            deploy.sentry.wait(timeout=1500)
        except amulet.TimeoutError:
            raise

    def test_web_frontend(self, deploy, sonarr):
        page = requests.get('http://{}:{}'.format(sonarr.info['public-address'], 8989))
        assert page.status_code == 200
        print(page)

    def test_reverseproxy(self, deploy, sonarr, haproxy):
        page = requests.get('http://{}:{}'.format(sonarr.info['public-address'], 8989))
        assert page.status_code == 200
        deploy.relate('sonarr:reverseproxy', 'haproxy:reverseproxy')
        time.sleep(30)
        page = requests.get('http://{}:{}/sonarr'.format(haproxy.info['public-address'], 80))
        assert page.status_code == 200

    def test_actions(self, deploy, sonarr):
        sonarr.ssh('sudo mkdir -p /home/sonarruser/.config/NzbDrone/Backups/scheduled')
        for action in sonarr.action_defined():
            uuid = sonarr.run_action(action)
            action_output = deploy.get_action_output(uuid, full_output=True)
            print(action)
            print(action_output)
            assert action_output['status'] == 'completed'
        # Restart so it's running not part of the test
        sonarr.run_action('start')

    # def test_action_update(self, deploy, sonarr):
    #     uuid = sonarr.run_action('update')
    #     action_output = deploy.get_action_output(uuid, full_output=True)
    #     print(action_output)
    #     assert action_output['status'] == 'completed'

    # def test_action_backup(self, deploy, sonarr):
    #     uuid = sonarr.run_action('backup')
    #     action_output = deploy.get_action_output(uuid, full_output=True)
    #     print(action_output)
    #     assert action_output['status'] == 'completed'

    #     # test we can access over http
    #     # page = requests.get('http://{}'.format(self.unit.info['public-address']))
    #     # self.assertEqual(page.status_code, 200)
    #     # Now you can use self.d.sentry[SERVICE][UNIT] to address each of the units and perform
    #     # more in-depth steps. Each self.d.sentry[SERVICE][UNIT] has the following methods:
    #     # - .info - An array of the information of that unit from Juju
    #     # - .file(PATH) - Get the details of a file on that unit
    #     # - .file_contents(PATH) - Get plain text output of PATH file from that unit
    #     # - .directory(PATH) - Get details of directory
    #     # - .directory_contents(PATH) - List files and folders in PATH on that unit
    #     # - .relation(relation, service:rel) - Get relation data from return service
