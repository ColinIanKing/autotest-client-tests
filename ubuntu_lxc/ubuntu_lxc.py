#
#
from autotest.client                        import test, utils
import platform

class ubuntu_lxc(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'lxc-tests',
            'liblxc1'
        ]

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        cmd = '/bin/sh %s/exercise' % self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
