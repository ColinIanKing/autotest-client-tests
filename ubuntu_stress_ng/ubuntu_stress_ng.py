#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_stress_ng(test.test):
    version = 1

    def initialize(self, test_name):
        self.job.require_gcc()

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        os.chdir(self.srcdir)
        cmd = 'git clone git://kernel.ubuntu.com/cking/stress-ng'
        self.results = utils.system_output(cmd, retain_output=True)

        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        cmd = 'make'
        self.results = utils.system_output(cmd, retain_output=True)

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))

        # Run each stressor for 60 seconds and gather some stats at the end
        #
        cmd = './stress-ng -v --verbose --timeout 60s --seq 0 --metrics --times'
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
