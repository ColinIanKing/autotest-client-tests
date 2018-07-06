#
#
import os
from autotest.client                        import test, utils
import platform

class ubuntu_unionmount_overlayfs_suite(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'git', 'python3',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.job.require_gcc()

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()
        if not os.path.exists('/lower'):
            os.mkdir('/lower')
        if not os.path.exists('/upper'):
            os.mkdir('/upper')
        os.chdir(self.srcdir)
        cmd = 'git clone http://kernel.ubuntu.com/git-repos/kernel-ppa/unionmount-testsuite.git'
        self.results = utils.system_output(cmd, retain_output=True)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'unionmount-testsuite'))

        if test_name == 'unionmount':
            cmd = './run --um'
            self.results = utils.system_output(cmd, retain_output=True)
        elif test_name == 'overlayfs':
            cmd = './run --ov'
            self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
