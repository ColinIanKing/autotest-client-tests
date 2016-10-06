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
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'gdb', 'git', 'docker.io', 'ubuntu-fan',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    def setup(self):
        pass

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
