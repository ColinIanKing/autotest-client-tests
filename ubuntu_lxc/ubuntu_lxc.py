#
#
from autotest.client                        import test, utils

class ubuntu_lxc(test.test):
    version = 1

    def initialize(self):
        pass

    def run_once(self, test_name):
        print('test name: "%s"' % test_name)
        cmd = '/usr/bin/%s' % test_name
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
