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
        series = platform.dist()[2]

        pkgs = [
            'build-essential'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.job.require_gcc()

    def setup(self):
        self.install_required_pkgs()
        shutil.copyfile(os.path.join(self.bindir, 'loop-test.c'),
                        os.path.join(self.srcdir, 'loop-test.c'))
        shutil.copyfile(os.path.join(self.bindir, 'Makefile'),
                        os.path.join(self.srcdir, 'Makefile'))

        os.chdir(self.srcdir)
        utils.make()

    def run_once(self, test_name):
        cmd = '%s/loop-test' % (self.srcdir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
