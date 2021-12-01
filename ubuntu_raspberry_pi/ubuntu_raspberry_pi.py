#
#
from autotest.client import test, utils
import os
import shutil

TEST_REPOSITORY = 'https://git.launchpad.net/~juergh/+git/raspi-rt'


class ubuntu_raspberry_pi(test.test):
    version = 1

    def initialize(self):
        pass

    def setup(self, test_name):
        os.chdir(self.srcdir)
        shutil.rmtree('raspi-rt', ignore_errors=True)
        cmd = 'git clone --depth=1 ' + TEST_REPOSITORY
        utils.system(cmd)
        os.chdir(os.path.join(self.srcdir, 'raspi-rt'))
        cmd = 'sudo ./install-deps'
        utils.system(cmd)

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        cmd = os.path.join(self.srcdir, 'raspi-rt', 'tests', test_name)
        utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
