from autotest.client                        import test,utils
from autotest.client.shared                 import error, software_manager

DEPENDENCIES=['libkeyutils-dev']

class ubuntu_cve_kernel(test.test):
    version = 1

    def initialize(self):
        self.job.require_gcc()
        utils.system('make -C %s/cves' % self.bindir)

    def run_once(self, cve, exit_on_error=True, set_time=True):
        print('*** %s ***' % cve)
        cmd = 'make -C %s/cves/%s check' % (self.bindir, cve)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
