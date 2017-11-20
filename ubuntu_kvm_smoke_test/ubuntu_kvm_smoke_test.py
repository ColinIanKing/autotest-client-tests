#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_kvm_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'cpu-checker',
            'uvtool',
        ]

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        cmd = 'kvm-ok'
        utils.system_output(cmd, retain_output=True)


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
        if platform.processor() == 'athlon':
            arch = platform.machine()
        else:
            arch = platform.processor()

        if arch in ['x86_64']:
            arch = 'amd64'
        elif arch in ['i686']:
            arch = 'i386'
        elif arch in ['aarch64']:
            arch = 'arm64'
        elif arch in ['ppc64le']:
            arch = 'ppc64el'

        cmd = 'sudo -u ubuntu %s/the-test %s' % (self.bindir, arch)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
