import os
import re
import platform
from autotest.client import utils, test
from autotest.client.shared import error

# test requires at least 2.6.26, will skip otherwise (check is internal)


class perfmon(test.test):
    version = 16

    def setup(self, tarball='perfmon-tests-0.3.tar.gz'):
        self.install_required_pkgs()
        self.job.require_gcc()
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.make()

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        utils.system(cmd)

    def initialize(self):
        self.results = []

    def run_once(self, dir=None, nprocs=None, args=''):
        cmd = self.srcdir + '/tests/pfm_tests' + args
        # self.results.append(utils.system_output(cmd, retain_output=True))
        if 'FAIL' in utils.system_output(cmd, retain_output=True):
            raise error.TestError('some perfmon tests failed')
