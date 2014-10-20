#
#
import os
from autotest.client                        import test, utils

class ubuntu_seccomp(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

        print(self.srcdir)
        os.makedirs(self.srcdir)
        os.chdir(self.srcdir)
        cmd = 'git clone https://github.com/redpig/seccomp.git'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'seccomp', 'tests'))
        cmd = 'make'
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = 'make run_tests'
        self.results = utils.system_output(cmd, retain_output=True)

    def run_once(self, test_name):
        pass

# vi:set ts=4 sw=4 expandtab syntax=python:
