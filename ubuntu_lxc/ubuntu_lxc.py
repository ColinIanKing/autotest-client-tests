#
#
from autotest.client                        import test, utils
import platform

class ubuntu_lxc(test.test):
    version = 1

    def install_required_pkgs(self):
        series = platform.dist()[2]

        pkgs = [
            'liblxc1'
        ]

        if series in ['precise', 'trusty', 'xenial', 'artful']:
            pkgs.append('lxc-tests')
        else:
            pkgs.append('lxc-utils')

        cmd = 'apt-get install --yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        series = platform.dist()[2]
        if series not in ['precise', 'trusty', 'xenial', 'artful']:
            self.results = utils.system_output('git clone https://github.com/lxc/lxc.git', retain_output=True)
            self.results = utils.system_output('sudo find lxc/src/tests -type f -name "lxc-test-*" -executable -exec cp {} /usr/bin/ \;', retain_output=True)

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        cmd = '/bin/sh %s/exercise' % self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
