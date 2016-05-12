from autotest.client                        import test,utils
from autotest.client.shared                 import error, software_manager

class ubuntu_load_livepatch_modules(test.test):
    version = 1

    def initialize(self):
        pass

    def run_once(self):
        cmd = '%s/load-livepatch-modules.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
