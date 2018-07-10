import os
from autotest.client import test
from autotest.client.shared import utils


class cyclictest(test.test):
    version = 2
    preserve_srcdir = True

    # git://git.kernel.org/pub/scm/linux/kernel/git/tglx/rt-tests.git
    def initialize(self):
        pass

    def setup(self):
        self.job.require_gcc()
        os.chdir(self.srcdir)
        utils.make()

    def execute(self, args='-t 10 -l 100000'):
        utils.system(self.srcdir + '/cyclictest ' + args)
