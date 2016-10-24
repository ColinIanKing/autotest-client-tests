#
#
from autotest.client                        import test, utils
import platform

class ubuntu_bpf_jit(test.test):
    version = 1

    def run_once(self, test_name):
        cmd = '%s/ubuntu_bpf_jit.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

        print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
