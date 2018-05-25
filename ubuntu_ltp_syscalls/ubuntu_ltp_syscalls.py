#
#
import os
import platform
from autotest.client                        import test, utils
from autotest.client.shared     import error

class ubuntu_ltp_syscalls(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()

        pkgs = [
            'build-essential', 'git', 'flex', 'automake',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        os.chdir(self.srcdir)
        cmd = 'git clone --depth=1 https://github.com/linux-test-project/ltp.git'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'ltp'))
        cmd = 'make autotools'
        self.results = utils.system_output(cmd, retain_output=True)
        cmd = './configure'
        self.results = utils.system_output(cmd, retain_output=True)
        cmd = 'make'
        self.results = utils.system_output(cmd, retain_output=True)
        cmd = 'make install'
        self.results = utils.system_output(cmd, retain_output=True)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir('/opt/ltp')

        cmd = './runltp -f %s' % test_name
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
