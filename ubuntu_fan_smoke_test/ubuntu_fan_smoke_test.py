#
#
import os
from autotest.client                        import test, utils
import multiprocessing

class ubuntu_fan_smoke_test(test.test):
    version = 1

    def initialize(self):
	utils.system_output('apt-get update || true', retain_output=True)
	utils.system_output('apt-get install docker.io --yes --force-yes', retain_output=True)
	utils.system_output('apt-get install ubuntu-fan --yes --force-yes', retain_output=True)

    def setup(self):
	pass

    def run_once(self, test_name):
        cmd = '%s/ubuntu_fan_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
