#
#
import os
from autotest.client                        import test, utils

class ubuntu_unionmount_overlayfs_suite(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        os.chdir(self.srcdir)
        cmd = 'git clone git://git.infradead.org/users/dhowells/unionmount-testsuite.git'
        self.results = utils.system_output(cmd, retain_output=True)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'unionmount-testsuite'))

        if test_name == 'unionmount':
            cmd = './run --um'
            self.results = utils.system_output(cmd, retain_output=True)
        elif test_name == 'overlayfs':
            cmd = './run --ov'
            self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
