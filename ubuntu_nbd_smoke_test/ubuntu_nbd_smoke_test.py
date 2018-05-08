#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_nbd_smoke_test(test.test):
    version = 0

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'nbd-server',
            'nbd-client',
            'gdb',
        ]
        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    def setup(self):
        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)
        os.chdir(self.srcdir)

    def run_once(self, test_name):
        #
        #  stress-ng "quick fire" short life tests
        #
        cmd = self.bindir + '/ubuntu_nbd_smoke_test.sh'
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        #print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
