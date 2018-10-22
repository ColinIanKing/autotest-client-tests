#
#
import platform
from autotest.client                        import test, utils

class ubuntu_sysdig_smoke_test(test.test):
    version = 99

    def install_required_pkgs(self):
        pkgs = [
            'sysdig'
        ]

        cmd = 'apt-get install --yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()

    def run_once(self, test_name):
        cmd = '%s/ubuntu_sysdig_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results

    def cleanup(self):
        cmd = 'modprobe -r sysdig_probe'
        self.results = utils.system_output(cmd, retain_output=False)

# vi:set ts=4 sw=4 expandtab syntax=python:
