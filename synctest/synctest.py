import os
import platform
from autotest.client import test
from autotest.client.shared import utils


class synctest(test.test):
    version = 1
    preserve_srcdir = True

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self):
        os.chdir(self.srcdir)
        utils.make()

    def run_once(self, len, loop, testdir=None):
        args = len + ' ' + loop
        output = os.path.join(self.srcdir, 'synctest ')
        if testdir:
            os.chdir(testdir)
        utils.system(output + args)
