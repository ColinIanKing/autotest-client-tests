#
#
import os
import platform
import shutil
from autotest.client                        import test, utils
from autotest.client                        import canonical

class ubuntu_futex(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential', 'git', 'ca-certificates'
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

        canonical.setup_proxy()

        os.chdir(self.srcdir)
        shutil.rmtree('futextest', ignore_errors=True)
        cmd = 'git clone --depth=1 https://git.kernel.org/pub/scm/linux/kernel/git/dvhart/futextest.git'
        self.results = utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'futextest'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        os.chdir(os.path.join(self.srcdir, 'futextest', 'functional'))
        cmd = 'sed -i s/lpthread/pthread/ Makefile'
        self.results = utils.system_output(cmd, retain_output=True)

        utils.make()

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'futextest', 'functional'))
        cmd = 'USE_COLOR=0 ./run.sh'

        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
