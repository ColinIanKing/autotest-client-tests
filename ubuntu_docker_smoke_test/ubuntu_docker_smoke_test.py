#
#
import os
import platform
import sys
from autotest.client                        import test, utils

class ubuntu_docker_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'docker.io',
        ]
        # Exception for arm64 and ppc64le on Trusty
        if platform.linux_distribution()[2] == 'trusty':
            if platform.machine() in ['aarch64', 'ppc64le']:
                print("Package docker.io is not available for this arch on Trusty.")
                sys.exit(0)
        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        cmd = 'sudo %s/the-test' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
