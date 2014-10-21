#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_stress_ng(test.test):
    version = 1

    def run_once(self, test_name):
        self.job.require_gcc()

        print(self.srcdir)
        os.chdir(self.srcdir)
        cmd = 'bzr branch lp:ubuntu/stress-ng'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = 'make'
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = './stress-ng --timeout 15m --all %d' % multiprocessing.cpu_count()
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
