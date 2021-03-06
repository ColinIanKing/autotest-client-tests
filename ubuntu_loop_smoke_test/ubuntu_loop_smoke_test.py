#
#
import os
import shutil
from autotest.client                        import test, utils
import platform

class ubuntu_loop_smoke_test(test.test):
    version = 0

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        shutil.copyfile(os.path.join(self.bindir, 'loop-test.c'),
                        os.path.join(self.srcdir, 'loop-test.c'))
        shutil.copyfile(os.path.join(self.bindir, 'Makefile'),
                        os.path.join(self.srcdir, 'Makefile'))

        os.chdir(self.srcdir)
        utils.make()

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        cmd = '%s/loop-test' % (self.srcdir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
