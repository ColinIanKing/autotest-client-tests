#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_kvm_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'uvtool',
        ]

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        pass

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        cmd = 'sudo -u ubuntu %s/the-test' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
