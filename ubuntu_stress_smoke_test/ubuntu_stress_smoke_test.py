#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_stress_smoke_test(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()

    def setup(self):
        utils.system_output('apt-get update', retain_output=True)
        cmd = 'apt-get install zlib1g-dev libbsd-dev libattr1-dev ' \
              'libkeyutils-dev libapparmor-dev apparmor libaio-dev ' \
              '--yes --allow-downgrades --allow-change-held-packages'
        utils.system_output(cmd, retain_output=True)
        os.chdir(self.srcdir)
        cmd = 'git clone git://kernel.ubuntu.com/cking/stress-ng'
        self.results = utils.system_output(cmd, retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'stress-ng'))
        self.results = utils.system_output('make', retain_output=True)

    def run_once(self, test_name):
        cmd = '%s/ubuntu_stress_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
