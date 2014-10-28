#
#
import os
from autotest.client                        import test, utils

class ubuntu_futex(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

        print(self.srcdir)
        os.makedirs(self.srcdir)
        os.chdir(self.srcdir)
        cmd = 'git clone git://git.kernel.org/pub/scm/linux/kernel/git/dvhart/futextest.git'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'futextest', 'functional'))
        cmd = 'sed -i s/lpthread/pthread/ Makefile'
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = 'make'
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = './run.sh'
        self.results = utils.system_output(cmd, retain_output=True)

    def run_once(self, test_name):
        pass

# vi:set ts=4 sw=4 expandtab syntax=python:
