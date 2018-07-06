#
#
import os
import platform
from autotest.client                        import test, utils
from autotest.client.shared     import error

class ubuntu_ltp(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]
        cloud  = os.environ['CLOUD']

        if cloud in ['gcp', 'gke', 'aws', 'azure']:
            raise error.TestError('This test suite does not run correctly on any of these clouds and needs to be investigated.')

        pkgs = [
            'automake',
            'bison',
            'build-essential',
            'byacc',
            'flex',
            'git',
            'libacl1-dev',
            'libaio-dev',
            'libcap-dev',
            'libmm-dev',
            'libnuma-dev',
            'libsctp-dev',
            'libselinux1-dev',
            'libssl-dev',
            'libtirpc-dev',
            'xfslibs-dev',
            'xfsprogs',
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
        os.chdir(self.srcdir)
        cmd = 'git clone https://github.com/linux-test-project/ltp.git'
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

        cmd = 'cat /opt/ltp/runtest/syscalls > /tmp/skip'
        utils.system_output(cmd)
        cmd = 'cat %s >> /tmp/skip' % os.path.join(self.bindir, 'skip')
        utils.system_output(cmd)

        cmd = './runltp -S /tmp/skip'
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
