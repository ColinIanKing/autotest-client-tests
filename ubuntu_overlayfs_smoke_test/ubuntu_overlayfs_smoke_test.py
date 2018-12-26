#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_overlayfs_smoke_test(test.test):
    version = 1

    def initialize(self):
        pass

    def setup(self):
        pass

    def run_once(self, test_name):
        stress_ng = os.path.join(self.srcdir, 'stress-ng', 'stress-ng')
        cmd = '%s/ubuntu_overlayfs_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
