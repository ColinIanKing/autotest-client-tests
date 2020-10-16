#
#
import os
import platform
import re
from autotest.client                        import test, utils

class ubuntu_fan_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'docker.io',
            'gdb',
            'git',
            'net-tools',
            'ubuntu-fan',
        ]

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def determine_underlay(self):
        underlay = 'bogus'
        cmd = 'ip address'
        output = utils.system_output(cmd, retain_output=False)
        for line in output.split('\n'):
            m = re.search('inet (\d+\.\d+)\.\d+\.\d+\/\d+ brd \d+\.\d+\.\d+\.\d+ scope', line)
            if m:
                underlay = '%s.0.0/16' % m.group(1)
                break
        return underlay

    def run_once(self, test_name):

        underlay = self.determine_underlay()

        os.chdir(self.bindir)
        cmd = './ubuntu_fan_smoke_test.sh %s' % (underlay)
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
