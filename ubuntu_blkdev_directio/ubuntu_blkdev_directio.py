#
#
import os
import platform
from autotest.client import test, utils

class ubuntu_blkdev_directio(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        utils.system('gcc %s/blkdev_dio_test.c -o %s/blkdev_dio_test' % (self.bindir, self.srcdir))

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        cmd = 'bash %s/ubuntu_blkdev_directio.sh %s/blkdev_dio_test' % (self.bindir, self.srcdir)
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        #print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
