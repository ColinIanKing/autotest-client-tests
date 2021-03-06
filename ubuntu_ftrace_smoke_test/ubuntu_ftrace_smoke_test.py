#
#
import platform
from autotest.client                        import test, utils

class ubuntu_ftrace_smoke_test(test.test):
    version = 1

    def run_once(self, test_name):
        cmd = '%s/ubuntu_ftrace_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
