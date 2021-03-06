#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_kvm_smoke_test(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()
        pkgs = [
            'cpu-checker',
            'uvtool',
            'uvtool-libvirt',
        ]
        # qemu-efi-aarch64 is needed for ARM64 Bionic, which is only
        # available since Artful
        if arch == 'aarch64' and series not in ['trusty', 'xenial']:
            pkgs.append('qemu-efi-aarch64')

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
        if test_name == 'setup':
            return
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

        # The smt (simultaneous multithreading) on ppc should be disabled for kvm
        # And it's done in the testing script.
        cmd = 'sudo -u %s %s/the-test %s' % (os.getlogin(), self.bindir, arch)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
