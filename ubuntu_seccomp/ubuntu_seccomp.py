#
#
import os
import platform
import shutil
from autotest.client                        import test, utils

class ubuntu_seccomp(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential', 'git', 'libtool', 'build-essential', 'autoconf', 'valgrind', 'gperf',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

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
        self.job.require_gcc()
        os.chdir(self.srcdir)
        shutil.rmtree('libseccomp', ignore_errors=True)
        cmd = 'git clone --depth=1 https://github.com/seccomp/libseccomp.git'
        self.results = utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'libseccomp'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        autogen = self.srcdir + '/libseccomp/autogen.sh'
        self.results = utils.system_output(autogen, retain_output=True)
        utils.configure()
        utils.make('check-build')

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        if test_name == 'setup':
            return
        os.chdir(os.path.join(self.srcdir, 'libseccomp', 'tests'))

        cmd = 'make check'
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
