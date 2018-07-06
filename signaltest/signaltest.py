import os
import platform
from autotest.client import test
from autotest.client.shared import utils


class signaltest(test.test):
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
        self.job.require_gcc()

    # git://git.kernel.org/pub/scm/linux/kernel/git/tglx/rt-tests.git
    def setup(self):
        self.install_required_pkgs()
        os.chdir(self.srcdir)
        utils.make()

    def execute(self, args='-t 10 -l 100000'):
        utils.system(self.srcdir + '/signaltest ' + args)
